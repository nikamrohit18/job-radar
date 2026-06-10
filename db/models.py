from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """One row per human user. Phase 1: a single default row (id=1). Phase 2: clerk_id-keyed."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(255))
    resume = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    """A raw job listing fetched from any source."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text)
    url = Column(String(1024), unique=True, index=True)  # deduplicate key
    source = Column(String(50))                           # "indeed", "hn", "manual", …
    date_posted = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class JobScore(Base):
    """AI scoring result — one per (user, job) pair."""
    __tablename__ = "job_scores"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ats_score = Column(Integer)
    interview_probability = Column(Integer)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    strengths = Column(JSON)
    gaps = Column(JSON)
    resume_tweaks = Column(JSON)
    summary = Column(Text)
    scored_at = Column(DateTime, default=datetime.utcnow)


class Application(Base):
    """Application pipeline tracker."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # applied -> screening -> interview -> offer -> rejected | withdrawn
    status = Column(String(50), default="applied", nullable=False)
    notes = Column(Text, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CoverLetter(Base):
    """AI-generated cover letter — one per (user, job, tone) combination."""
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    tone = Column(String(50), default="professional")
    generated_at = Column(DateTime, default=datetime.utcnow)


class InterviewPrep(Base):
    """AI-generated interview prep guide — one per (user, job) pair."""
    __tablename__ = "interview_preps"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)  # JSON-serialized PrepResult
    generated_at = Column(DateTime, default=datetime.utcnow)
