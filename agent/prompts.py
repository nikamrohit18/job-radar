from .models import Job

SYSTEM = """You are a senior technical recruiter and hiring manager with deep expertise in:
- Applicant Tracking Systems (ATS) and how they score resumes against job descriptions
- What makes candidates stand out for technical roles
- Realistic salary ranges by role, location, and years of experience
- Common gaps between job requirements and candidate profiles

Your task: analyze a job posting against a candidate's resume and give an honest, specific assessment.
Be realistic — not overly optimistic. Provide USD salary estimates."""


def score_prompt(job: Job, resume: str) -> str:
    return f"""Score this job opportunity for the candidate based on their resume.

## Job Posting
**Title:** {job.title}
**Company:** {job.company}
**Location:** {job.location}

{job.description}

---

## Candidate Resume

{resume}

---

Analyze the fit and provide:
- `ats_score` (0-100): how well the candidate's keywords and experience match the requirements
- `interview_probability` (0-100): realistic % chance of getting an interview, given competition
- `salary_min` / `salary_max`: realistic USD salary range for this role at the candidate's level
- `strengths`: the candidate's genuine advantages for THIS specific role (be specific)
- `gaps`: missing skills or experience that meaningfully reduce their chances
- `resume_tweaks`: specific keyword or phrasing changes to improve ATS score for this job
- `summary`: 2-3 sentences of honest overall assessment"""
