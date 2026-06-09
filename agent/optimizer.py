"""
Resume optimizer -- aggregates resume_tweaks from all scored jobs,
identifies universal improvements (not job-specific), and ranks them by impact.
"""

from anthropic import Anthropic
from pydantic import BaseModel

client = Anthropic()
MODEL = "claude-sonnet-4-6"


class TweakRecommendation(BaseModel):
    action: str        # One imperative sentence: "Add X to Y"
    section: str       # "summary" | "skills" | "experience" | "certifications" | "projects"
    why: str           # Plain-English impact, 1-2 sentences, no buzzwords
    jobs_flagged: int  # How many scored jobs surfaced this theme


class OptimizerResult(BaseModel):
    top_tweaks: list[TweakRecommendation]  # Ranked: highest-impact universal changes first
    total_jobs_analyzed: int
    assessment: str    # 2-3 plain sentences on overall resume health


SYSTEM = """You are a resume analyst. You receive raw resume improvement suggestions collected by scoring multiple job applications for one candidate. Your job is to synthesise them into a ranked action plan.

How to think about it:
- Some suggestions appear across many different roles. These are UNIVERSAL -- they should be fixed regardless of which job the candidate applies for.
- Some suggestions only appear for one specific job (e.g., "add MongoDB" when only one job requires MongoDB). These are JOB-SPECIFIC -- useful for that role but not worth a permanent resume change.
- Keep only UNIVERSAL suggestions. Discard job-specific ones.
- Rank what remains by expected impact: keyword density issues first (ATS), then framing issues (recruiter), then nice-to-haves.

Writing rules -- apply these to every field you write:
- No em-dashes
- No buzzwords: leverage, robust, synergy, transformative, cutting-edge, spearhead, champion, holistic, impactful, actionable
- "action" field: one verb-led sentence. "Add...", "Move...", "Rewrite...", "Include...", "Replace..."
- "why" field: plain English, 1-2 sentences. Say what the ATS or recruiter problem is, not why it would be "beneficial"
- "assessment" field: 2-3 honest sentences on resume strength and the main gap pattern across all scored roles"""


def analyze(resume: str, all_tweaks: list[str], job_count: int) -> OptimizerResult:
    """
    Synthesise resume tweaks from multiple scored jobs.
    Returns ranked universal recommendations, highest-impact first.
    """
    if not all_tweaks:
        return OptimizerResult(
            top_tweaks=[],
            total_jobs_analyzed=job_count,
            assessment="No resume tweaks collected yet. Score more jobs to generate recommendations.",
        )

    tweaks_block = "\n".join(f"- {t}" for t in all_tweaks)

    prompt = f"""The candidate has been scored against {job_count} job applications. Each application produced a list of suggested resume improvements. All suggestions are collected below.

Current resume:
{resume}

---

Raw suggestions ({len(all_tweaks)} total, some duplicates or near-duplicates):
{tweaks_block}

---

Task:
1. Group near-duplicate suggestions. Count how many distinct jobs produced each theme.
2. Keep only suggestions that appeared across multiple jobs or that are clearly structural gaps regardless of the specific role.
3. Discard suggestions that only matter for one specific job's niche technology or domain.
4. Rank the keepers by expected improvement to ATS pass rate and recruiter clarity.
5. Return max 8 recommendations, most impactful first.
6. Set total_jobs_analyzed to {job_count}.
7. Write assessment as 2-3 plain sentences: what is strong about this resume across all scored roles, and what is the main recurring gap."""

    response = client.messages.parse(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_format=OptimizerResult,
    )

    if response.parsed_output is None:
        raise ValueError(f"Optimizer failed (stop_reason={response.stop_reason})")

    return response.parsed_output
