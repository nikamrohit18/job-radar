from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agent.models import Job as PydanticJob
from agent.scorer import score_job
from api.deps import get_current_user, get_db
from api.schemas import FetchIn, FetchOut, JobOut, ManualJobIn, ScoreOut
from db import models as orm
from scrapers import indeed, remotive, wwr

router = APIRouter()


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


def _resolve_resume(user: orm.User) -> str:
    if user.resume:
        return user.resume
    fp = Path("data/resume.md")
    if fp.exists():
        return fp.read_text()
    raise HTTPException(
        status_code=400,
        detail="No resume on file. Upload via PUT /users/me/resume",
    )


@router.get("", response_model=list[JobOut])
def list_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    rows = (
        db.query(orm.JobScore, orm.Job)
        .join(orm.Job, orm.JobScore.job_id == orm.Job.id)
        .filter(orm.JobScore.user_id == user.id)
        .order_by(orm.JobScore.ats_score.desc())
        .limit(limit)
        .all()
    )
    return [_job_to_out(job, score) for score, job in rows]


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
    resume = _resolve_resume(user)

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
        pydantic_job = PydanticJob(
            title=db_job.title,
            company=db_job.company,
            location=db_job.location,
            description=db_job.description,
            url=db_job.url,
            source=db_job.source,
        )
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
    """Create a job from pasted JD text (e.g. copied from LinkedIn) and score it immediately."""
    resume = _resolve_resume(user)

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

    pydantic_job = PydanticJob(
        title=db_job.title,
        company=db_job.company,
        location=db_job.location or "",
        description=db_job.description,
        url=db_job.url or "",
        source=db_job.source,
    )
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
