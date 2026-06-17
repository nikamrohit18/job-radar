from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agent import interview_prep as prep_agent
from api.deps import get_current_user, get_db
from api.routes.jobs import _resolve_resume, _to_pydantic_job
from api.schemas import PrepGapQuestionOut, PrepIn, PrepOut, PrepQuestionOut
from db import models as orm

router = APIRouter()


def _prep_to_out(job_id: int, db_prep: orm.InterviewPrep, cached: bool) -> PrepOut:
    result = prep_agent.PrepResult.model_validate_json(db_prep.content)
    return PrepOut(
        id=db_prep.id,
        job_id=job_id,
        company_snapshot=result.company_snapshot,
        key_themes=result.key_themes,
        technical_questions=[PrepQuestionOut(**q.model_dump()) for q in result.technical_questions],
        behavioral_questions=[PrepQuestionOut(**q.model_dump()) for q in result.behavioral_questions],
        gap_questions=[PrepGapQuestionOut(**q.model_dump()) for q in (result.gap_questions or [])],
        generated_at=db_prep.generated_at,
        cached=cached,
    )


@router.get("/{job_id}/prep", response_model=PrepOut)
def get_prep(
    job_id: int,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    existing = (
        db.query(orm.InterviewPrep)
        .filter_by(job_id=job_id, user_id=user.id)
        .first()
    )
    if not existing:
        raise HTTPException(
            status_code=404,
            detail=f"No interview prep found for job #{job_id}. "
                   "Generate one via POST /jobs/{id}/prep",
        )
    return _prep_to_out(job_id, existing, cached=True)


@router.post("/{job_id}/prep", response_model=PrepOut)
def generate_prep(
    job_id: int,
    body: PrepIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    job = db.query(orm.Job).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job #{job_id} not found")

    existing = (
        db.query(orm.InterviewPrep)
        .filter_by(job_id=job_id, user_id=user.id)
        .first()
    )
    if existing and not body.regen:
        return _prep_to_out(job_id, existing, cached=True)

    resume = _resolve_resume(user)
    score = db.query(orm.JobScore).filter_by(job_id=job_id, user_id=user.id).first()
    gaps = score.gaps if score else None

    pydantic_job = _to_pydantic_job(job)
    result = prep_agent.generate(pydantic_job, resume, gaps=gaps)

    if existing:
        existing.content = result.model_dump_json()
        existing.generated_at = datetime.now()
        db.commit()
        db.refresh(existing)
        return _prep_to_out(job_id, existing, cached=False)

    db_prep = orm.InterviewPrep(
        job_id=job.id,
        user_id=user.id,
        content=result.model_dump_json(),
    )
    db.add(db_prep)
    db.commit()
    db.refresh(db_prep)
    return _prep_to_out(job_id, db_prep, cached=False)
