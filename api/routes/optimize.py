from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agent import optimizer
from api.deps import get_current_user, get_db
from api.routes.jobs import _resolve_resume
from api.schemas import OptimizeOut, TweakOut
from db import models as orm

router = APIRouter()


@router.post("", response_model=OptimizeOut)
def run_optimizer(
    min_jobs: int = 2,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    scores = db.query(orm.JobScore).filter_by(user_id=user.id).all()
    job_count = len(scores)

    if job_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No scored jobs yet. Fetch and score jobs first via POST /jobs/fetch",
        )
    if job_count < min_jobs:
        raise HTTPException(
            status_code=400,
            detail=f"Only {job_count} job(s) scored. Need {min_jobs}+ for optimizer. "
                   f"Lower min_jobs or fetch more jobs.",
        )

    all_tweaks: list[str] = []
    for s in scores:
        if s.resume_tweaks:
            all_tweaks.extend(s.resume_tweaks)

    resume = _resolve_resume(user)
    result = optimizer.analyze(resume, all_tweaks, job_count)

    return OptimizeOut(
        total_jobs_analyzed=result.total_jobs_analyzed,
        assessment=result.assessment,
        top_tweaks=[
            TweakOut(
                section=t.section,
                action=t.action,
                why=t.why,
                jobs_flagged=t.jobs_flagged,
            )
            for t in result.top_tweaks
        ],
    )
