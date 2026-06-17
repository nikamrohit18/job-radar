"""Pydantic request/response schemas for the job-radar API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

class ScoreOut(BaseModel):
    ats_score: int
    interview_probability: int
    salary_min: int
    salary_max: int
    strengths: list[str]
    gaps: list[str]
    missing_keywords: list[str]
    resume_tweaks: list[str]
    summary: str
    scored_at: datetime
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    date_posted: Optional[datetime] = None
    created_at: datetime
    score: Optional[ScoreOut] = None

    model_config = {"from_attributes": True}


class FetchIn(BaseModel):
    source: str = "wwr"
    query: str = "software engineer python"
    location: str = "remote"
    days: int = 3
    limit: int = 20


class FetchOut(BaseModel):
    fetched: int
    new: int
    skipped: int
    jobs: list[JobOut]


class ManualJobIn(BaseModel):
    jd_text: str
    title: str
    company: str
    location: str = ""
    url: str = ""


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

class ApplyIn(BaseModel):
    note: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD


class StatusIn(BaseModel):
    new_status: str


class NoteIn(BaseModel):
    text: str


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    status: str
    notes: Optional[str] = None
    applied_at: Optional[datetime] = None
    updated_at: datetime
    job: Optional[JobOut] = None
    score: Optional[ScoreOut] = None

    model_config = {"from_attributes": True}


class PipelineOut(BaseModel):
    applied: list[ApplicationOut] = []
    screening: list[ApplicationOut] = []
    interview: list[ApplicationOut] = []
    offer: list[ApplicationOut] = []
    rejected: list[ApplicationOut] = []
    withdrawn: list[ApplicationOut] = []


# ---------------------------------------------------------------------------
# Cover Letter
# ---------------------------------------------------------------------------

class CoverLetterIn(BaseModel):
    tone: str = "professional"
    regen: bool = False


class CoverLetterOut(BaseModel):
    id: int
    content: str
    tone: str
    generated_at: datetime
    cached: bool = False

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Interview Prep
# ---------------------------------------------------------------------------

class PrepIn(BaseModel):
    regen: bool = False


class PrepQuestionOut(BaseModel):
    question: str
    talking_point: str


class PrepGapQuestionOut(BaseModel):
    gap: str
    question: str
    talking_point: str


class PrepOut(BaseModel):
    id: int
    job_id: int
    company_snapshot: str
    key_themes: list[str]
    technical_questions: list[PrepQuestionOut]
    behavioral_questions: list[PrepQuestionOut]
    gap_questions: list[PrepGapQuestionOut]
    generated_at: datetime
    cached: bool = False


# ---------------------------------------------------------------------------
# Tailored Resume Rewrite
# ---------------------------------------------------------------------------

class ResumeRewriteIn(BaseModel):
    regen: bool = False


class ResumeRewriteOut(BaseModel):
    id: int
    content: str
    generated_at: datetime
    cached: bool = False

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Resume Optimizer
# ---------------------------------------------------------------------------

class TweakOut(BaseModel):
    section: str
    action: str
    why: str
    jobs_flagged: int


class OptimizeOut(BaseModel):
    total_jobs_analyzed: int
    assessment: str
    top_tweaks: list[TweakOut]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class UserOut(BaseModel):
    id: int
    clerk_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateIn(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None


# ---------------------------------------------------------------------------
# Resume versions
# ---------------------------------------------------------------------------

class ResumeVersionIn(BaseModel):
    content: str
    label: Optional[str] = None


class ResumeVersionOut(BaseModel):
    id: int
    content: str
    label: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
