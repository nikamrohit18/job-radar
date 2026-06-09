#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # must run before importing scorer (Anthropic client reads API key on init)

from agent import cover_letter, interview_prep, optimizer
from agent.models import Job
from agent.scorer import score_job
from db import models as orm
from db.session import get_or_create_default_user, init_db, SessionLocal
from scrapers import indeed, remotive, wwr
from tracker import commands as tracker


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _sep(char: str = "=", width: int = 60) -> str:
    return char * width


def _days_ago(dt: datetime) -> str:
    if dt is None:
        return "unknown"
    delta = (datetime.now() - dt).days
    if delta == 0:
        return "today"
    if delta == 1:
        return "1 day ago"
    return f"{delta} days ago"


def _print_score(job_id: int, title: str, company: str, s, applied: bool = False, detail: bool = True) -> None:
    applied_tag = "  [applied]" if applied else ""
    print(f"\n{_sep()}")
    print(f"  #{job_id}  {title} @ {company}{applied_tag}")
    print(_sep())
    print(f"  ATS Score:             {s.ats_score}/100")
    print(f"  Interview Probability: {s.interview_probability}%")
    print(f"  Salary Estimate:       ${s.salary_min:,} – ${s.salary_max:,}")
    print(f"\n  {s.summary}")
    if detail:
        print(f"\n  Strengths:")
        for item in s.strengths:
            print(f"    + {item}")
        print(f"\n  Gaps:")
        for item in s.gaps:
            print(f"    - {item}")
        print(f"\n  Resume Tweaks:")
        for item in s.resume_tweaks:
            print(f"    * {item}")
    print()


# ---------------------------------------------------------------------------
# Commands -- scoring
# ---------------------------------------------------------------------------

def cmd_sample(_args) -> None:
    """Score the hardcoded sample job -- useful for testing without API calls."""
    resume = Path("data/resume.md").read_text()
    job = Job(**json.loads(Path("data/sample_job.json").read_text()))
    print(f"Scoring: {job.title} at {job.company}...")
    result = score_job(job, resume)
    _print_score(0, job.title, job.company, result.score)


def cmd_fetch(args) -> None:
    """Fetch jobs from a source, score new listings, persist everything to DB."""
    source = args.source or os.getenv("JOB_SOURCE", "wwr")
    query = args.query or os.getenv("INDEED_QUERY", "software engineer python")
    location = args.location or os.getenv("INDEED_LOCATION", "remote")
    days_old = args.days or int(os.getenv("INDEED_DAYS_OLD", "3"))

    init_db()
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)
        resume = Path("data/resume.md").read_text()

        print(f"Fetching from {source}: query='{query}' | location='{location}'")
        if source == "indeed":
            raw_jobs = indeed.fetch_jobs(query, location, days_old)
        elif source == "remotive":
            raw_jobs = remotive.fetch_jobs(query=query)
        elif source == "wwr":
            raw_jobs = wwr.fetch_jobs(query=query)
        else:
            print(f"Unknown source '{source}'. Supported: wwr (default), remotive, indeed")
            return
        print(f"  {len(raw_jobs)} listings retrieved")

        new_db_jobs: list[orm.Job] = []
        skipped = 0
        for raw in raw_jobs:
            if not raw["url"]:
                continue
            if db.query(orm.Job).filter_by(url=raw["url"]).first():
                skipped += 1
                continue
            db_job = orm.Job(**raw)
            db.add(db_job)
            db.flush()
            new_db_jobs.append(db_job)

        db.commit()
        print(f"  {len(new_db_jobs)} new  |  {skipped} already in DB")

        if not new_db_jobs:
            print("\nNothing new to score. Try a wider search or increase --days.")
            return

        scored: list[tuple[orm.Job, object]] = []
        for db_job in new_db_jobs:
            pydantic_job = Job(
                title=db_job.title,
                company=db_job.company,
                location=db_job.location,
                description=db_job.description,
                url=db_job.url,
                source=db_job.source,
            )
            print(f"Scoring: {db_job.title} at {db_job.company}...")
            try:
                result = score_job(pydantic_job, resume)
                s = result.score
                db.add(orm.JobScore(
                    job_id=db_job.id,
                    user_id=user.id,
                    ats_score=s.ats_score,
                    interview_probability=s.interview_probability,
                    salary_min=s.salary_min,
                    salary_max=s.salary_max,
                    strengths=s.strengths,
                    gaps=s.gaps,
                    resume_tweaks=s.resume_tweaks,
                    summary=s.summary,
                ))
                db.commit()
                scored.append((db_job, s))
            except Exception as exc:
                print(f"  ! Scoring failed for '{db_job.title}': {exc}")

        scored.sort(key=lambda x: x[1].ats_score, reverse=True)
        applied_ids = tracker.get_applied_job_ids(db, user.id)
        print(f"\n{_sep()}")
        print(f"  {len(scored)} JOBS SCORED -- ranked by ATS fit")
        for db_job, s in scored:
            _print_score(db_job.id, db_job.title, db_job.company, s,
                         applied=db_job.id in applied_ids, detail=False)

    finally:
        db.close()


def cmd_list(args) -> None:
    """Show top scored jobs stored in the DB, ranked by ATS score."""
    init_db()
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)
        rows = (
            db.query(orm.JobScore, orm.Job)
            .join(orm.Job, orm.JobScore.job_id == orm.Job.id)
            .order_by(orm.JobScore.ats_score.desc())
            .limit(args.limit)
            .all()
        )
        if not rows:
            print("No scored jobs in database yet. Run:  python main.py fetch")
            return

        applied_ids = tracker.get_applied_job_ids(db, user.id)
        print(f"\n{_sep()}")
        print(f"  TOP {len(rows)} SCORED JOBS  --  use #ID with 'apply' command")
        for score, job in rows:
            _print_score(job.id, job.title, job.company, score,
                         applied=job.id in applied_ids, detail=False)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Commands -- cover letter
# ---------------------------------------------------------------------------

def _display_cover_letter(job, content: str, tone: str, cached: bool) -> None:
    cache_note = "  (cached -- use --regen to regenerate)" if cached else ""
    print(f"\n{_sep()}")
    print(f"  COVER LETTER  --  #{job.id}  {job.title} @ {job.company}")
    print(f"  Tone: {tone}{cache_note}")
    print(_sep())
    print()
    for para in content.split("\n\n"):
        para = para.strip()
        if para:
            print(f"  {para}")
            print()
    words = len(content.split())
    print(f"  [{words} words]")
    print(f"\n  Save to file:  python main.py coverletter {job.id} --save")
    print()


def _save_cover_letter(job, content: str) -> None:
    covers_dir = Path("covers")
    covers_dir.mkdir(exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in job.company)[:30]
    path = covers_dir / f"cover_letter_{job.id}_{safe}.txt"
    path.write_text(content, encoding="utf-8")
    print(f"  Saved: {path}\n")


def cmd_coverletter(args) -> None:
    """Generate (or retrieve) a tailored cover letter for a scored job."""
    init_db()
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)

        job = db.query(orm.Job).filter_by(id=args.job_id).first()
        if not job:
            print(f"\n  Error: Job #{args.job_id} not found. Run: python main.py list\n")
            return

        tone = args.tone or "professional"
        existing = (
            db.query(orm.CoverLetter)
            .filter_by(job_id=args.job_id, user_id=user.id, tone=tone)
            .first()
        )

        if existing and not args.regen:
            _display_cover_letter(job, existing.content, existing.tone, cached=True)
            if args.save:
                _save_cover_letter(job, existing.content)
            return

        resume = Path("data/resume.md").read_text()
        print(f"\nGenerating cover letter for: {job.title} @ {job.company}  [tone: {tone}]")

        pydantic_job = Job(
            title=job.title, company=job.company, location=job.location,
            description=job.description, url=job.url, source=job.source,
        )
        content = cover_letter.generate(pydantic_job, resume, tone=tone)

        if existing:
            existing.content = content
            existing.generated_at = datetime.now()
        else:
            db.add(orm.CoverLetter(
                job_id=job.id, user_id=user.id, content=content, tone=tone,
            ))
        db.commit()

        _display_cover_letter(job, content, tone, cached=False)
        if args.save:
            _save_cover_letter(job, content)

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Commands -- application tracker
# ---------------------------------------------------------------------------

def cmd_apply(args) -> None:
    """Mark a job as applied and start tracking it."""
    init_db()
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)

        applied_at = None
        if args.date:
            try:
                applied_at = datetime.strptime(args.date, "%Y-%m-%d")
            except ValueError:
                print(f"Invalid date format '{args.date}'. Use YYYY-MM-DD.")
                return

        app = tracker.apply(db, user.id, args.job_id, note=args.note, applied_at=applied_at)
        job = db.query(orm.Job).filter_by(id=args.job_id).first()
        score = db.query(orm.JobScore).filter_by(job_id=args.job_id, user_id=user.id).first()

        print(f"\n  Tracking: #{job.id}  {job.title} @ {job.company}")
        print(f"  Status:   applied  (as of {app.applied_at.strftime('%Y-%m-%d')})")
        if score:
            print(f"  ATS:      {score.ats_score}/100  |  Interview: {score.interview_probability}%")
        print(f"\n  Next: python main.py status {job.id} screening")
        print(f"        python main.py note {job.id} \"add a note\"")
        print()
    except ValueError as e:
        print(f"\n  Error: {e}\n")
    finally:
        db.close()


def cmd_status(args) -> None:
    """Update the status of a tracked application."""
    init_db()
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)
        app = tracker.update_status(db, user.id, args.job_id, args.new_status)
        job = db.query(orm.Job).filter_by(id=args.job_id).first()
        print(f"\n  #{job.id}  {job.title} @ {job.company}")
        print(f"  Status updated -> {app.status}\n")
    except ValueError as e:
        print(f"\n  Error: {e}\n")
    finally:
        db.close()


def cmd_note(args) -> None:
    """Add a note to a tracked application."""
    init_db()
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)
        tracker.add_note(db, user.id, args.job_id, args.text)
        job = db.query(orm.Job).filter_by(id=args.job_id).first()
        print(f"\n  Note added to #{job.id}  {job.title} @ {job.company}\n")
    except ValueError as e:
        print(f"\n  Error: {e}\n")
    finally:
        db.close()


def cmd_pipeline(_args) -> None:
    """Display the full application pipeline, grouped by status."""
    init_db()
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)
        pipeline = tracker.get_pipeline(db, user.id)

        total = sum(len(v) for v in pipeline.values())
        if total == 0:
            print("\n  No applications tracked yet.")
            print("  Step 1:  python main.py list          (see scored job IDs)")
            print("  Step 2:  python main.py apply <id>    (start tracking)\n")
            return

        active = sum(len(pipeline[s]) for s in ["applied", "screening", "interview"])
        offers = len(pipeline["offer"])
        closed = len(pipeline["rejected"]) + len(pipeline["withdrawn"])

        print(f"\n{_sep()}")
        print(f"  APPLICATION PIPELINE  --  {active} active  |  {offers} offer  |  {closed} closed")
        print(_sep())

        STATUS_ORDER = ["applied", "screening", "interview", "offer", "rejected", "withdrawn"]
        STATUS_LABEL = {
            "applied":   "APPLIED",
            "screening": "SCREENING",
            "interview": "INTERVIEW",
            "offer":     "OFFER",
            "rejected":  "REJECTED",
            "withdrawn": "WITHDRAWN",
        }

        for status in STATUS_ORDER:
            apps = pipeline[status]
            label = STATUS_LABEL[status]
            bar = "-" * max(0, 46 - len(label) - len(str(len(apps))))
            print(f"\n  * {label} ({len(apps)})  {bar}")

            if not apps:
                print("    (none)")
                continue

            for app, job, score in apps:
                ats_str = f"ATS {score.ats_score}/100" if score else "unscored"
                time_str = _days_ago(app.updated_at)

                follow_up = ""
                if status == "applied":
                    days_since = (datetime.now() - app.updated_at).days
                    if days_since >= tracker.FOLLOW_UP_DAYS:
                        follow_up = "  ! follow up"

                print(f"    #{job.id}  {job.title} @ {job.company}")
                print(f"        {time_str}  |  {ats_str}{follow_up}")

                if app.notes:
                    first_line = app.notes.split("\n")[0]
                    print(f"        > {first_line}")

        print()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Commands -- resume optimizer
# ---------------------------------------------------------------------------

def _save_optimization_report(result, resume_path: Path) -> Path:
    opt_dir = Path("optimizations")
    opt_dir.mkdir(exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    path = opt_dir / f"resume_optimizer_{date_str}.md"

    lines = [
        f"# Resume Optimization Report -- {date_str}",
        f"",
        f"Jobs analyzed: {result.total_jobs_analyzed}",
        f"Resume: {resume_path}",
        f"",
        f"## Assessment",
        f"",
        result.assessment,
        f"",
        f"## Recommended Changes ({len(result.top_tweaks)})",
        f"",
    ]
    for i, t in enumerate(result.top_tweaks, 1):
        lines += [
            f"### {i}. [{t.section}] {t.action}",
            f"",
            f"Flagged by {t.jobs_flagged} of {result.total_jobs_analyzed} jobs scored.",
            f"",
            t.why,
            f"",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def cmd_optimize(args) -> None:
    """Synthesise resume_tweaks from all scored jobs into ranked improvement recommendations."""
    init_db()
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)

        scores = (
            db.query(orm.JobScore)
            .filter_by(user_id=user.id)
            .all()
        )
        job_count = len(scores)
        min_jobs = args.min_jobs

        if job_count == 0:
            print("\n  No scored jobs yet.")
            print("  Fetch and score some jobs first:  python main.py fetch -q 'head of AI'\n")
            return

        if job_count < min_jobs:
            print(f"\n  Only {job_count} job(s) scored. Optimizer works best with {min_jobs}+ scored jobs.")
            print(f"  Use --min-jobs 1 to run anyway, or fetch more jobs first.\n")
            return

        all_tweaks: list[str] = []
        for s in scores:
            if s.resume_tweaks:
                all_tweaks.extend(s.resume_tweaks)

        resume_path = Path("data/resume.md")
        resume = resume_path.read_text()

        print(f"\n  Analyzing {job_count} scored jobs ({len(all_tweaks)} raw suggestions)...")
        result = optimizer.analyze(resume, all_tweaks, job_count)

        print(f"\n{_sep()}")
        print(f"  RESUME OPTIMIZER  --  {result.total_jobs_analyzed} jobs analyzed")
        print(_sep())
        print(f"\n  Assessment:")
        for line in result.assessment.split(". "):
            line = line.strip()
            if line:
                print(f"  {line}{'.' if not line.endswith('.') else ''}")
        print()

        if not result.top_tweaks:
            print("  No universal improvements identified yet. Score more targeted jobs.")
            print()
            return

        print(f"  TOP {len(result.top_tweaks)} IMPROVEMENTS  --  ranked by expected impact")
        print()
        for i, t in enumerate(result.top_tweaks, 1):
            flagged = f"{t.jobs_flagged}/{result.total_jobs_analyzed} jobs"
            print(f"  {i}. [{t.section}] {t.action}")
            print(f"     Flagged by {flagged}")
            print(f"     > {t.why}")
            print()

        if args.save:
            path = _save_optimization_report(result, resume_path)
            print(f"  Report saved: {path}\n")
        else:
            print(f"  Save full report:  python main.py optimize --save\n")

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Commands -- interview prep
# ---------------------------------------------------------------------------

def _display_prep(job, result: "interview_prep.PrepResult", cached: bool) -> None:
    cache_note = "  (cached -- use --regen to regenerate)" if cached else ""
    print(f"\n{_sep()}")
    print(f"  INTERVIEW PREP  --  #{job.id}  {job.title} @ {job.company}{cache_note}")
    print(_sep())

    print(f"\n  COMPANY SNAPSHOT")
    print(f"  {result.company_snapshot}")

    print(f"\n  KEY THEMES  --  thread these through every answer")
    for theme in result.key_themes:
        print(f"    * {theme}")

    print(f"\n{'-' * 60}")
    print(f"  TECHNICAL QUESTIONS ({len(result.technical_questions)})")
    print(f"{'-' * 60}")
    for i, q in enumerate(result.technical_questions, 1):
        print(f"\n  {i}. {q.question}")
        for line in q.talking_point.split(". "):
            line = line.strip()
            if line:
                print(f"     > {line}{'.' if not line.endswith('.') else ''}")

    print(f"\n{'-' * 60}")
    print(f"  BEHAVIORAL QUESTIONS ({len(result.behavioral_questions)})")
    print(f"{'-' * 60}")
    for i, q in enumerate(result.behavioral_questions, 1):
        print(f"\n  {i}. {q.question}")
        for line in q.talking_point.split(". "):
            line = line.strip()
            if line:
                print(f"     > {line}{'.' if not line.endswith('.') else ''}")

    if result.gap_questions:
        print(f"\n{'-' * 60}")
        print(f"  GAP / TOUGH QUESTIONS ({len(result.gap_questions)})")
        print(f"  These are the probing questions based on your scored gaps.")
        print(f"{'-' * 60}")
        for i, q in enumerate(result.gap_questions, 1):
            print(f"\n  {i}. Gap: {q.gap}")
            print(f"     Q: \"{q.question}\"")
            for line in q.talking_point.split(". "):
                line = line.strip()
                if line:
                    print(f"     > {line}{'.' if not line.endswith('.') else ''}")

    print(f"\n  Save as file:  python main.py prep {job.id} --save")
    print()


def _save_prep_report(job, result: "interview_prep.PrepResult") -> Path:
    prep_dir = Path("prep")
    prep_dir.mkdir(exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in job.company)[:30]
    path = prep_dir / f"interview_prep_{job.id}_{safe}.md"

    lines = [
        f"# Interview Prep -- #{job.id} {job.title} @ {job.company}",
        f"",
        f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
        f"",
        f"## Company Snapshot",
        f"",
        result.company_snapshot,
        f"",
        f"## Key Themes",
        f"",
    ]
    for theme in result.key_themes:
        lines.append(f"- {theme}")
    lines += ["", "## Technical Questions", ""]
    for i, q in enumerate(result.technical_questions, 1):
        lines += [f"### {i}. {q.question}", f"", f"> {q.talking_point}", f""]
    lines += ["## Behavioral Questions", ""]
    for i, q in enumerate(result.behavioral_questions, 1):
        lines += [f"### {i}. {q.question}", f"", f"> {q.talking_point}", f""]
    if result.gap_questions:
        lines += ["## Gap / Tough Questions", ""]
        for i, q in enumerate(result.gap_questions, 1):
            lines += [
                f"### {i}. Gap: {q.gap}",
                f"",
                f'**Q:** "{q.question}"',
                f"",
                f"> {q.talking_point}",
                f"",
            ]

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def cmd_prep(args) -> None:
    """Generate an interview prep guide for a scored job."""
    init_db()
    db = SessionLocal()
    try:
        user = get_or_create_default_user(db)

        job = db.query(orm.Job).filter_by(id=args.job_id).first()
        if not job:
            print(f"\n  Error: Job #{args.job_id} not found. Run: python main.py list\n")
            return

        existing = (
            db.query(orm.InterviewPrep)
            .filter_by(job_id=args.job_id, user_id=user.id)
            .first()
        )

        if existing and not args.regen:
            result = interview_prep.PrepResult.model_validate_json(existing.content)
            _display_prep(job, result, cached=True)
            if args.save:
                path = _save_prep_report(job, result)
                print(f"  Saved: {path}\n")
            return

        score = db.query(orm.JobScore).filter_by(job_id=args.job_id, user_id=user.id).first()
        gaps = score.gaps if score else None

        resume = Path("data/resume.md").read_text()
        print(f"\n  Generating interview prep for: {job.title} @ {job.company}...")
        if score:
            print(f"  Using score data (ATS {score.ats_score}/100, {len(gaps or [])} gaps identified)")

        pydantic_job = Job(
            title=job.title, company=job.company, location=job.location,
            description=job.description, url=job.url, source=job.source,
        )
        result = interview_prep.generate(pydantic_job, resume, gaps=gaps)

        if existing:
            existing.content = result.model_dump_json()
            existing.generated_at = datetime.now()
        else:
            db.add(orm.InterviewPrep(
                job_id=job.id,
                user_id=user.id,
                content=result.model_dump_json(),
            ))
        db.commit()

        _display_prep(job, result, cached=False)
        if args.save:
            path = _save_prep_report(job, result)
            print(f"  Saved: {path}\n")

    finally:
        db.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="job-radar -- AI-powered job scoring & application tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "scoring:\n"
            "  python main.py fetch -q 'head of AI' -s wwr\n"
            "  python main.py list\n"
            "  python main.py sample\n"
            "\ntracking:\n"
            "  python main.py apply 4\n"
            "  python main.py apply 4 --date 2026-06-01 --note 'via recruiter'\n"
            "  python main.py status 4 screening\n"
            "  python main.py note 4 'Interview call Friday 2pm'\n"
            "  python main.py pipeline\n"
            "\ncover letters:\n"
            "  python main.py coverletter 4\n"
            "  python main.py coverletter 4 --tone startup\n"
            "  python main.py coverletter 4 --tone brief --save\n"
            "  python main.py coverletter 4 --regen\n"
            "\nresume optimizer:\n"
            "  python main.py optimize\n"
            "  python main.py optimize --min-jobs 1\n"
            "  python main.py optimize --save\n"
            "\ninterview prep:\n"
            "  python main.py prep 4\n"
            "  python main.py prep 4 --save\n"
            "  python main.py prep 4 --regen\n"
        ),
    )
    sub = parser.add_subparsers(dest="command")

    # --- scoring ---
    sub.add_parser("sample", help="Score the sample job (dev/test)")

    fp = sub.add_parser("fetch", help="Fetch jobs from a source and score them")
    fp.add_argument("--source", "-s", metavar="SOURCE",
                    help="Job source: wwr (default), remotive, indeed")
    fp.add_argument("--query", "-q", metavar="QUERY",
                    help="Search query (overrides INDEED_QUERY env var)")
    fp.add_argument("--location", "-l", metavar="LOC",
                    help="Location, e.g. 'remote' or 'Bangkok' (overrides INDEED_LOCATION)")
    fp.add_argument("--days", "-d", type=int, metavar="N",
                    help="Listings from last N days (overrides INDEED_DAYS_OLD)")

    lp = sub.add_parser("list", help="List top scored jobs from the database")
    lp.add_argument("--limit", "-n", type=int, default=20, metavar="N",
                    help="Number of results to show (default: 20)")

    # --- tracking ---
    ap = sub.add_parser("apply", help="Mark a job as applied and start tracking it")
    ap.add_argument("job_id", type=int, metavar="ID",
                    help="Job ID from 'python main.py list'")
    ap.add_argument("--date", metavar="YYYY-MM-DD",
                    help="Date you applied (defaults to today)")
    ap.add_argument("--note", metavar="TEXT",
                    help="Optional note (e.g. 'applied via recruiter')")

    sp = sub.add_parser("status", help="Update the status of a tracked application")
    sp.add_argument("job_id", type=int, metavar="ID", help="Job ID")
    sp.add_argument("new_status", metavar="STATUS",
                    help=f"New status: {', '.join(tracker.STATUSES)}")

    np = sub.add_parser("note", help="Add a note to a tracked application")
    np.add_argument("job_id", type=int, metavar="ID", help="Job ID")
    np.add_argument("text", metavar="TEXT", help="Note text")

    sub.add_parser("pipeline", help="Show the full application pipeline")

    # --- cover letter ---
    cp = sub.add_parser("coverletter", help="Generate a tailored cover letter for a job")
    cp.add_argument("job_id", type=int, metavar="ID",
                    help="Job ID from 'python main.py list'")
    cp.add_argument("--tone", "-t", metavar="TONE", default="professional",
                    help="Tone: professional (default), startup, brief")
    cp.add_argument("--regen", action="store_true",
                    help="Regenerate even if a cover letter already exists")
    cp.add_argument("--save", action="store_true",
                    help="Save the cover letter to covers/cover_letter_<id>_<company>.txt")

    # --- optimizer ---
    op = sub.add_parser("optimize", help="Analyze scored jobs and recommend resume improvements")
    op.add_argument("--min-jobs", type=int, default=2, metavar="N",
                    help="Minimum scored jobs required to run (default: 2)")
    op.add_argument("--save", action="store_true",
                    help="Save the full report to optimizations/resume_optimizer_<date>.md")

    # --- interview prep ---
    pp = sub.add_parser("prep", help="Generate an interview prep guide for a job")
    pp.add_argument("job_id", type=int, metavar="ID",
                    help="Job ID from 'python main.py list'")
    pp.add_argument("--regen", action="store_true",
                    help="Regenerate even if a prep guide already exists")
    pp.add_argument("--save", action="store_true",
                    help="Save the guide to prep/interview_prep_<id>_<company>.md")

    args = parser.parse_args()

    dispatch = {
        "fetch":       cmd_fetch,
        "list":        cmd_list,
        "apply":       cmd_apply,
        "status":      cmd_status,
        "note":        cmd_note,
        "pipeline":    cmd_pipeline,
        "coverletter": cmd_coverletter,
        "optimize":    cmd_optimize,
        "prep":        cmd_prep,
        "sample":      cmd_sample,
    }

    fn = dispatch.get(args.command, cmd_sample)
    fn(args)


if __name__ == "__main__":
    main()
