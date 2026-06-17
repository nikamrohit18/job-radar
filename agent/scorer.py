from anthropic import Anthropic
from .models import Job, ScoreResult, ScoredJob
from .prompts import SYSTEM, job_prompt, resume_block

client = Anthropic()
MODEL = "claude-sonnet-4-6"


def score_job(job: Job, resume: str) -> ScoredJob:
    # The resume is its own cached content block: when scoring many jobs against
    # the same resume in one fetch run, Claude reuses the cached prefix instead of
    # reprocessing the full resume on every call (no quality impact, lower cost).
    # Blocks under ~1024 tokens are simply not cached -- this degrades silently.
    response = client.messages.parse(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": resume_block(resume), "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": job_prompt(job)},
            ],
        }],
        output_format=ScoreResult,
    )
    if response.parsed_output is None:
        raise ValueError(f"Scoring failed (stop_reason={response.stop_reason})")
    return ScoredJob(job=job, score=response.parsed_output)
