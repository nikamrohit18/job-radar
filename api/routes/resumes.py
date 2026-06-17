from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.schemas import ResumeVersionIn, ResumeVersionOut
from db import models as orm

router = APIRouter()


def _to_out(v: orm.ResumeVersion) -> ResumeVersionOut:
    return ResumeVersionOut(
        id=v.id, content=v.content, label=v.label,
        is_active=v.is_active, created_at=v.created_at,
    )


@router.get("", response_model=list[ResumeVersionOut])
def list_resumes(
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    versions = (
        db.query(orm.ResumeVersion)
        .filter_by(user_id=user.id)
        .order_by(orm.ResumeVersion.created_at.desc())
        .all()
    )
    return [_to_out(v) for v in versions]


@router.post("", response_model=ResumeVersionOut)
def save_resume(
    body: ResumeVersionIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    """Save a new resume version and make it active immediately -- matches the
    old paste-and-replace UX. Past versions are kept, never overwritten."""
    db.query(orm.ResumeVersion).filter_by(user_id=user.id, is_active=True).update({"is_active": False})
    version = orm.ResumeVersion(
        user_id=user.id,
        content=body.content,
        label=body.label or None,
        is_active=True,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return _to_out(version)


@router.put("/{version_id}/activate", response_model=ResumeVersionOut)
def activate_resume(
    version_id: int,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    version = db.query(orm.ResumeVersion).filter_by(id=version_id, user_id=user.id).first()
    if not version:
        raise HTTPException(status_code=404, detail=f"Resume version #{version_id} not found")
    db.query(orm.ResumeVersion).filter_by(user_id=user.id, is_active=True).update({"is_active": False})
    version.is_active = True
    db.commit()
    db.refresh(version)
    return _to_out(version)
