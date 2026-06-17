from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agent import resume_rewrite as rewrite_agent
from agent.models import Job as PydanticJob
from api.deps import get_current_user, get_db
from api.routes.jobs import _resolve_resume
from api.schemas import ResumeRewriteIn, ResumeRewriteOut
from db import models as orm

router = APIRouter()


@router.get("/{job_id}/resume", response_model=ResumeRewriteOut)
def get_tailored_resume(
    job_id: int,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    existing = (
        db.query(orm.TailoredResume)
        .filter_by(job_id=job_id, user_id=user.id)
        .first()
    )
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"No tailored resume found for job #{job_id}. "
                   "Generate one via POST /jobs/{id}/resume",
        )
    return ResumeRewriteOut(
        id=existing.id,
        content=existing.content,
        generated_at=existing.generated_at,
        cached=True,
    )


@router.post("/{job_id}/resume", response_model=ResumeRewriteOut)
def generate_tailored_resume(
    job_id: int,
    body: ResumeRewriteIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    job = db.query(orm.Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job #{job_id} not found")

    existing = (
        db.query(orm.TailoredResume)
        .filter_by(job_id=job_id, user_id=user.id)
        .first()
    )
    if existing and not body.regen:
        return ResumeRewriteOut(
            id=existing.id, content=existing.content,
            generated_at=existing.generated_at, cached=True,
        )

    resume = _resolve_resume(user)
    score = db.query(orm.JobScore).filter_by(job_id=job_id, user_id=user.id).first()
    gaps = score.gaps if score else None
    missing_keywords = score.missing_keywords if score else None

    pydantic_job = PydanticJob(
        title=job.title, company=job.company, location=job.location,
        description=job.description, url=job.url, source=job.source,
    )
    content = rewrite_agent.generate(pydantic_job, resume, gaps=gaps, missing_keywords=missing_keywords)

    if existing:
        existing.content = content
        existing.generated_at = datetime.now()
        db.commit()
        db.refresh(existing)
        return ResumeRewriteOut(
            id=existing.id, content=existing.content,
            generated_at=existing.generated_at, cached=False,
        )

    db_resume = orm.TailoredResume(
        job_id=job.id, user_id=user.id, content=content,
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return ResumeRewriteOut(
        id=db_resume.id, content=db_resume.content,
        generated_at=db_resume.generated_at, cached=False,
    )
