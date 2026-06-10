import os
from typing import Generator

from sqlalchemy import create_engine
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
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)


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
