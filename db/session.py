import os
from datetime import datetime
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from .models import Base, User

_raw_url = os.getenv("DATABASE_URL", "sqlite:///./job_radar.db")
# Neon / older Heroku-style URLs use postgres:// — SQLAlchemy requires postgresql://
DATABASE_URL = (
    "postgresql://" + _raw_url[len("postgres://"):]
    if _raw_url.startswith("postgres://")
    else _raw_url
)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
# pool_pre_ping: Neon suspends its compute when idle and silently drops connections —
# without this, the first query after a suspend fails with "SSL connection has been
# closed unexpectedly" instead of transparently reconnecting.
engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)
    _ensure_missing_keywords_column()
    _ensure_job_score_archive_columns()
    _migrate_resume_versions()


def _ensure_missing_keywords_column() -> None:
    """job_scores predates the missing_keywords column -- add it if an older DB lacks it."""
    inspector = inspect(engine)
    if "job_scores" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("job_scores")}
    if "missing_keywords" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE job_scores ADD COLUMN missing_keywords JSON"))


def _ensure_job_score_archive_columns() -> None:
    """job_scores predates is_deleted/deleted_at (soft-delete) -- add them if missing."""
    inspector = inspect(engine)
    if "job_scores" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("job_scores")}
    with engine.begin() as conn:
        if "is_deleted" not in columns:
            conn.execute(text("ALTER TABLE job_scores ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE"))
        if "deleted_at" not in columns:
            conn.execute(text("ALTER TABLE job_scores ADD COLUMN deleted_at TIMESTAMP"))


def _migrate_resume_versions() -> None:
    """One-time, idempotent: users.resume (single text field) predates the
    resume_versions table. Backfill each user's existing resume as their first
    active version, then drop the old column -- after this runs once, the old
    column is gone, so re-running is a no-op (it returns as soon as the column
    is missing)."""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "resume" not in columns:
        return
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT id, resume FROM users WHERE resume IS NOT NULL AND resume != ''")
        ).fetchall()
        for user_id, resume_content in rows:
            already_migrated = conn.execute(
                text("SELECT COUNT(*) FROM resume_versions WHERE user_id = :uid"),
                {"uid": user_id},
            ).scalar()
            if already_migrated:
                continue
            conn.execute(
                text(
                    "INSERT INTO resume_versions (user_id, content, label, is_active, created_at) "
                    "VALUES (:user_id, :content, :label, :is_active, :created_at)"
                ),
                {
                    "user_id": user_id,
                    "content": resume_content,
                    "label": "Migrated resume",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                },
            )
        conn.execute(text("ALTER TABLE users DROP COLUMN resume"))


def get_db() -> Generator:
    """FastAPI dependency — yield a DB session and close it on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_or_create_default_user(db) -> User:
    """Return the Phase-1 default user (id=1), creating it on first run."""
    user = db.query(User).filter_by(id=1).first()
    if not user:
        user = User(
            id=1,
            email=os.getenv("USER_EMAIL", "user@localhost"),
            name=os.getenv("USER_NAME", "Default User"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
