"""
Application tracker — core data logic.
Display/CLI layer lives in main.py; this module only touches the database.
"""

from datetime import datetime
from typing import Optional

from db import models as orm

# Ordered pipeline stages
STATUSES = ["applied", "screening", "interview", "offer", "rejected", "withdrawn"]

# Flag "applied" applications that haven't moved after this many days
FOLLOW_UP_DAYS = 7


def _now() -> datetime:
    return datetime.now()


def _stamp() -> str:
    return _now().strftime("%Y-%m-%d")


def _prepend_note(existing: Optional[str], entry: str) -> str:
    return f"{entry}\n{existing}" if existing else entry


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def apply(
    db,
    user_id: int,
    job_id: int,
    note: Optional[str] = None,
    applied_at: Optional[datetime] = None,
) -> orm.Application:
    """Create an Application record. Raises ValueError if job not found or already tracked."""
    job = db.query(orm.Job).filter_by(id=job_id).first()
    if not job:
        raise ValueError(
            f"Job #{job_id} not found in database.\n"
            "  Run: python main.py list   to see available job IDs."
        )

    existing = db.query(orm.Application).filter_by(job_id=job_id, user_id=user_id).first()
    if existing:
        raise ValueError(
            f"Already tracking #{job_id} ({job.title} @ {job.company}).\n"
            f"  Current status: {existing.status}\n"
            "  Use:  python main.py status <id> <new_status>\n"
            "  Or:   python main.py note <id> \"your note\""
        )

    initial_note = _prepend_note(note, f"[{_stamp()}] Applied")
    app = orm.Application(
        job_id=job_id,
        user_id=user_id,
        status="applied",
        applied_at=applied_at or _now(),
        updated_at=_now(),
        notes=initial_note,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def update_status(
    db,
    user_id: int,
    job_id: int,
    new_status: str,
) -> orm.Application:
    """Move application to a new status. Appends a log entry to notes."""
    if new_status not in STATUSES:
        raise ValueError(
            f"Invalid status '{new_status}'.\n"
            f"  Valid statuses: {', '.join(STATUSES)}"
        )

    app = _get_application_or_raise(db, user_id, job_id)
    old_status = app.status
    app.status = new_status
    app.updated_at = _now()
    app.notes = _prepend_note(app.notes, f"[{_stamp()}] {old_status} -> {new_status}")

    db.commit()
    db.refresh(app)
    return app


def add_note(
    db,
    user_id: int,
    job_id: int,
    note: str,
) -> orm.Application:
    """Prepend a timestamped note to an application's note history."""
    app = _get_application_or_raise(db, user_id, job_id)
    app.notes = _prepend_note(app.notes, f"[{_stamp()}] {note}")
    app.updated_at = _now()

    db.commit()
    db.refresh(app)
    return app


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def get_pipeline(
    db,
    user_id: int,
) -> dict[str, list[tuple[orm.Application, orm.Job, Optional[orm.JobScore]]]]:
    """Return all applications grouped by status, including job and score info."""
    rows = (
        db.query(orm.Application, orm.Job, orm.JobScore)
        .join(orm.Job, orm.Application.job_id == orm.Job.id)
        .outerjoin(
            orm.JobScore,
            (orm.JobScore.job_id == orm.Application.job_id)
            & (orm.JobScore.user_id == orm.Application.user_id),
        )
        .filter(orm.Application.user_id == user_id)
        .order_by(orm.Application.updated_at.desc())
        .all()
    )

    pipeline: dict[str, list] = {s: [] for s in STATUSES}
    for app, job, score in rows:
        bucket = app.status if app.status in pipeline else "withdrawn"
        pipeline[bucket].append((app, job, score))

    return pipeline


def get_applied_job_ids(db, user_id: int) -> set[int]:
    """Return the set of job IDs that already have an Application record."""
    rows = db.query(orm.Application.job_id).filter_by(user_id=user_id).all()
    return {r[0] for r in rows}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_application_or_raise(db, user_id: int, job_id: int) -> orm.Application:
    app = db.query(orm.Application).filter_by(job_id=job_id, user_id=user_id).first()
    if not app:
        job = db.query(orm.Job).filter_by(id=job_id).first()
        job_label = f"({job.title} @ {job.company})" if job else ""
        raise ValueError(
            f"No application tracked for job #{job_id} {job_label}.\n"
            f"  Start tracking with:  python main.py apply {job_id}"
        )
    return app
