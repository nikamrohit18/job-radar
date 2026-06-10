from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agent import cover_letter as cl_agent
from agent.models import Job as PydanticJob
from api.deps import get_current_user, get_db
from api.routes.jobs import _resolve_resume
from api.schemas import CoverLetterIn, CoverLetterOut
from db import models as orm

router = APIRouter()


@router.get("/{job_id}/coverletter", response_model=CoverLetterOut)
def get_cover_letter(
    job_id: int,
    tone: str = "professional",
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    existing = (
        db.query(orm.CoverLetter)
        .filter_by(job_id=job_id, user_id=user.id, tone=tone)
        .first()
    )
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"No cover letter found for job #{job_id} with tone '{tone}'. "
                   "Generate one via POST /jobs/{id}/coverletter",
        )
    return CoverLetterOut(
        id=existing.id,
        content=existing.content,
        tone=existing.tone,
        generated_at=existing.generated_at,
        cached=True,
    )


@router.post("/{job_id}/coverletter", response_model=CoverLetterOut)
def generate_cover_letter(
    job_id: int,
    body: CoverLetterIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    job = db.query(orm.Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job #{job_id} not found")

    existing = (
        db.query(orm.CoverLetter)
        .filter_by(job_id=job_id, user_id=user.id, tone=body.tone)
        .first()
    )
    if existing and not body.regen:
        return CoverLetterOut(
            id=existing.id,
            content=existing.content,
            tone=existing.tone,
            generated_at=existing.generated_at,
            cached=True,
        )

    resume = _resolve_resume(user)
    pydantic_job = PydanticJob(
        title=job.title, company=job.company, location=job.location,
        description=job.description, url=job.url, source=job.source,
    )
    content = cl_agent.generate(pydantic_job, resume, tone=body.tone)

    if existing:
        existing.content = content
        existing.generated_at = datetime.now()
        db.commit()
        db.refresh(existing)
        return CoverLetterOut(
            id=existing.id, content=existing.content,
            tone=existing.tone, generated_at=existing.generated_at, cached=False,
        )

    db_cl = orm.CoverLetter(
        job_id=job.id, user_id=user.id, content=content, tone=body.tone,
    )
    db.add(db_cl)
    db.commit()
    db.refresh(db_cl)
    return CoverLetterOut(
        id=db_cl.id, content=db_cl.content,
        tone=db_cl.tone, generated_at=db_cl.generated_at, cached=False,
    )
