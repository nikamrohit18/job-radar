from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.routes.jobs import _job_to_out, _score_to_out
from api.schemas import ApplicationOut, ApplyIn, NoteIn, PipelineOut, StatusIn
from db import models as orm
from tracker import commands as tracker

router = APIRouter()


def _app_to_out(
    app: orm.Application,
    job: orm.Job | None = None,
    score: orm.JobScore | None = None,
) -> ApplicationOut:
    return ApplicationOut(
        id=app.id,
        job_id=app.job_id,
        status=app.status,
        notes=app.notes,
        applied_at=app.applied_at,
        updated_at=app.updated_at,
        job=_job_to_out(job, score) if job else None,
        score=_score_to_out(score) if score else None,
    )


@router.post("/{job_id}/apply", response_model=ApplicationOut)
def apply(
    job_id: int,
    body: ApplyIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    applied_at = None
    if body.date:
        try:
            applied_at = datetime.strptime(body.date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format '{body.date}'. Use YYYY-MM-DD.",
            )
    try:
        app = tracker.apply(db, user.id, job_id, note=body.note, applied_at=applied_at)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    job = db.query(orm.Job).filter_by(id=job_id).first()
    score = db.query(orm.JobScore).filter_by(job_id=job_id, user_id=user.id).first()
    return _app_to_out(app, job, score)


@router.put("/{job_id}/status", response_model=ApplicationOut)
def update_status(
    job_id: int,
    body: StatusIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    try:
        app = tracker.update_status(db, user.id, job_id, body.new_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    job = db.query(orm.Job).filter_by(id=job_id).first()
    score = db.query(orm.JobScore).filter_by(job_id=job_id, user_id=user.id).first()
    return _app_to_out(app, job, score)


@router.post("/{job_id}/note", response_model=ApplicationOut)
def add_note(
    job_id: int,
    body: NoteIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    try:
        app = tracker.add_note(db, user.id, job_id, body.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    job = db.query(orm.Job).filter_by(id=job_id).first()
    score = db.query(orm.JobScore).filter_by(job_id=job_id, user_id=user.id).first()
    return _app_to_out(app, job, score)


@router.get("/pipeline", response_model=PipelineOut)
def get_pipeline(
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    pipeline_data = tracker.get_pipeline(db, user.id)
    result: dict[str, list[ApplicationOut]] = {}
    for status, entries in pipeline_data.items():
        result[status] = [_app_to_out(app, job, score) for app, job, score in entries]
    return PipelineOut(**result)
