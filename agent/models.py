from pydantic import BaseModel


class Job(BaseModel):
    title: str
    company: str
    location: str
    description: str
    url: str = ""
    source: str = ""


class ScoreResult(BaseModel):
    ats_score: int               # 0–100, keyword/requirement match
    interview_probability: int   # 0–100, realistic % chance
    salary_min: int              # USD
    salary_max: int              # USD
    strengths: list[str]
    gaps: list[str]
    resume_tweaks: list[str]
    summary: str                 # 2–3 sentence assessment


class ScoredJob(BaseModel):
    job: Job
    score: ScoreResult
