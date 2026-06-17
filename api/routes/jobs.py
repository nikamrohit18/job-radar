from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from agent.models import Job as PydanticJob
from agent.scorer import score_job
from api.deps import get_current_user, get_db
from api.schemas import FetchIn, FetchOut, JobOut, ManualJobIn, ScoreOut
from db import models as orm
from scrapers import indeed, remotive, wwr

router = APIRouter()

SORT_COLUMNS = {
    "ats_score": orm.JobScore.ats_score,
    "interview_probability": orm.JobScore.interview_probability,
    "scored_at": orm.JobScore.scored_at,
    "date_posted": orm.Job.date_posted,
}


def _score_to_out(s: orm.JobScore) -> ScoreOut:
    return ScoreOut(
        ats_score=s.ats_score,
        interview_probability=s.interview_probability,
        salary_min=s.salary_min,
        salary_max=s.salary_max,
        strengths=s.strengths or [],
        gaps=s.gaps or [],
        missing_keywords=s.missing_keywords or [],
        resume_tweaks=s.resume_tweaks or [],
        summary=s.summary or "",
        scored_at=s.scored_at,
        is_deleted=s.is_deleted,
        deleted_at=s.deleted_at,
    )


def _job_to_out(job: orm.Job, score: orm.JobScore | None = None) -> JobOut:
    return JobOut(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        url=job.url,
        source=job.source,
        date_posted=job.date_posted,
        created_at=job.created_at,
        score=_score_to_out(score) if score else None,
    )


def _to_pydantic_job(job: orm.Job) -> PydanticJob:
    """agent.models.Job requires str fields; ORM location/url are nullable (manual jobs especially)."""
    return PydanticJob(
        title=job.title,
        company=job.company,
        location=job.location or "",
        description=job.description,
        url=job.url or "",
        source=job.source or "",
    )


def _resolve_resume(user: orm.User, db: Session) -> str:
    """Each user's active ResumeVersion is the only source -- no shared
    fallback file.

    (A previous version fell back to the server-local data/resume.md when a
    user had none on file. That file is Rohit's personal resume; falling back
    to it would leak his resume to any other signed-up user who hasn't saved
    their own yet. The CLI entry point in main.py still reads data/resume.md
    directly and is unaffected -- it's single-user by design.)
    """
    active = db.query(orm.ResumeVersion).filter_by(user_id=user.id, is_active=True).first()
    if active:
        return active.content
    raise HTTPException(
        status_code=400,
        detail="No resume on file. Save one via POST /users/me/resumes",
    )


@router.get("", response_model=list[JobOut])
def list_jobs(
    limit: int = 30,
    archived: bool = False,
    location: str | None = None,
    company: str | None = None,
    source: str | None = None,
    min_score: int | None = None,
    sort_by: str = "ats_score",
    sort_dir: str = "desc",
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    query = (
        db.query(orm.JobScore, orm.Job)
        .join(orm.Job, orm.JobScore.job_id == orm.Job.id)
        .filter(orm.JobScore.user_id == user.id, orm.JobScore.is_deleted == archived)
    )
    if location:
        query = query.filter(orm.Job.location.ilike(f"%{location}%"))
    if company:
        query = query.filter(orm.Job.company.ilike(f"%{company}%"))
    if source:
        query = query.filter(orm.Job.source == source)
    if min_score is not None:
        query = query.filter(orm.JobScore.ats_score >= min_score)

    column = SORT_COLUMNS.get(sort_by, orm.JobScore.ats_score)
    query = query.order_by(asc(column) if sort_dir == "asc" else desc(column))

    rows = query.limit(limit).all()
    return [_job_to_out(job, score) for score, job in rows]


@router.delete("/{job_id}", response_model=JobOut)
def archive_job(
    job_id: int,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    """Soft-delete only -- flags this user's score so it drops off the active
    dashboard, but the row (and any cover letters / preps / tailored resumes
    generated against it) is never removed. See is_deleted on JobScore."""
    score = db.query(orm.JobScore).filter_by(job_id=job_id, user_id=user.id).first()
    if not score:
        raise HTTPException(status_code=404, detail=f"No scored job #{job_id} for this user")
    score.is_deleted = True
    score.deleted_at = datetime.utcnow()
    db.commit()
    job = db.query(orm.Job).filter_by(id=job_id).first()
    return _job_to_out(job, score)


@router.post("/{job_id}/restore", response_model=JobOut)
def restore_job(
    job_id: int,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    score = db.query(orm.JobScore).filter_by(job_id=job_id, user_id=user.id).first()
    if not score:
        raise HTTPException(status_code=404, detail=f"No scored job #{job_id} for this user")
    score.is_deleted = False
    score.deleted_at = None
    db.commit()
    job = db.query(orm.Job).filter_by(id=job_id).first()
    return _job_to_out(job, score)


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    job = db.query(orm.Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job #{job_id} not found")
    score = db.query(orm.JobScore).filter_by(job_id=job_id, user_id=user.id).first()
    return _job_to_out(job, score)


@router.post("/fetch", response_model=FetchOut)
def fetch_jobs(
    body: FetchIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    resume = _resolve_resume(user, db)

    source = body.source
    if source == "indeed":
        raw_jobs = indeed.fetch_jobs(body.query, body.location, body.days)
    elif source == "remotive":
        raw_jobs = remotive.fetch_jobs(query=body.query, limit=body.limit)
    elif source == "wwr":
        raw_jobs = wwr.fetch_jobs(query=body.query, limit=body.limit)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source '{source}'. Supported: wwr, remotive, indeed",
        )

    new_db_jobs: list[orm.Job] = []
    skipped = 0
    for raw in raw_jobs:
        if not raw.get("url"):
            continue
        if db.query(orm.Job).filter_by(url=raw["url"]).first():
            skipped += 1
            continue
        db_job = orm.Job(**raw)
        db.add(db_job)
        db.flush()
        new_db_jobs.append(db_job)
    db.commit()

    scored_jobs: list[JobOut] = []
    for db_job in new_db_jobs:
        pydantic_job = _to_pydantic_job(db_job)
        try:
            result = score_job(pydantic_job, resume)
            s = result.score
            db_score = orm.JobScore(
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
            )
            db.add(db_score)
            db.commit()
            scored_jobs.append(_job_to_out(db_job, db_score))
        except Exception:
            scored_jobs.append(_job_to_out(db_job, None))

    scored_jobs.sort(
        key=lambda j: j.score.ats_score if j.score else -1,
        reverse=True,
    )

    return FetchOut(
        fetched=len(raw_jobs),
        new=len(new_db_jobs),
        skipped=skipped,
        jobs=scored_jobs,
    )


@router.post("/manual", response_model=JobOut)
def create_manual_job(
    body: ManualJobIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    """Create a job from pasted JD text (e.g. copied from LinkedIn) and score it immediately.

    `url` is a unique column on Job. If the pasted Listing URL matches a job that
    already exists -- this user re-pasted the same listing, or it was already
    auto-fetched -- reuse that job/score instead of inserting a duplicate row
    (which would otherwise crash with a database integrity error).
    """
    resume = _resolve_resume(user, db)

    db_job = db.query(orm.Job).filter_by(url=body.url).first() if body.url else None
    if db_job is None:
        db_job = orm.Job(
            title=body.title,
            company=body.company,
            location=body.location or None,
            description=body.jd_text,
            url=body.url or None,
            source="manual",
        )
        db.add(db_job)
        db.commit()

    existing_score = db.query(orm.JobScore).filter_by(job_id=db_job.id, user_id=user.id).first()
    if existing_score:
        if existing_score.is_deleted:
            existing_score.is_deleted = False
            existing_score.deleted_at = None
            db.commit()
        return _job_to_out(db_job, existing_score)

    pydantic_job = _to_pydantic_job(db_job)
    try:
        result = score_job(pydantic_job, resume)
    except Exception:
        return _job_to_out(db_job, None)

    s = result.score
    db_score = orm.JobScore(
        job_id=db_job.id,
        user_id=user.id,
        ats_score=s.ats_score,
        interview_probability=s.interview_probability,
        salary_min=s.salary_min,
        salary_max=s.salary_max,
        strengths=s.strengths,
        gaps=s.gaps,
        missing_keywords=s.missing_keywords,
        resume_tweaks=s.resume_tweaks,
        summary=s.summary,
    )
    db.add(db_score)
    db.commit()

    return _job_to_out(db_job, db_score)
