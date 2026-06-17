from .models import Job

SYSTEM = """You are a senior technical recruiter and hiring manager with deep expertise in:
- Applicant Tracking Systems (ATS) and how they score resumes against job descriptions
- What makes candidates stand out for technical roles
- Realistic salary ranges by role, location, and years of experience
- Common gaps between job requirements and candidate profiles

Your task: analyze a job posting against a candidate's resume and give an honest, specific assessment.
Be realistic — not overly optimistic. Provide USD salary estimates."""


def resume_block(resume: str) -> str:
    """The resume, as its own block so it can be prompt-cached across multiple
    score_job() calls in the same fetch run (same user, many jobs, one resume)."""
    return f"""## Candidate Resume

{resume}"""


def job_prompt(job: Job) -> str:
    """Per-job instructions -- everything that changes from one score_job() call
    to the next. Kept separate from resume_block() so the resume can be cached."""
    return f"""Score this job opportunity for the candidate based on their resume.

## Job Posting
**Title:** {job.title}
**Company:** {job.company}
**Location:** {job.location}

{job.description}

---

Analyze the fit and provide:
- `ats_score` (0-100): how well the candidate's keywords and experience match the requirements
- `interview_probability` (0-100): realistic % chance of getting an interview, given competition
- `salary_min` / `salary_max`: realistic USD salary range for this role at the candidate's level
- `strengths`: the candidate's genuine advantages for THIS specific role (be specific)
- `gaps`: missing skills or experience that meaningfully reduce their chances (substance, not phrasing)
- `missing_keywords`: exact terms or phrases from the job posting (tools, certifications, methodologies, titles) that an ATS would scan for and that are missing or underrepresented in the resume, even if the candidate has the underlying experience
- `resume_tweaks`: specific keyword or phrasing changes to improve ATS score for this job
- `summary`: 2-3 sentences of honest overall assessment"""
