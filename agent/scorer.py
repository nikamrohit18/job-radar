from anthropic import Anthropic
from .models import Job, ScoreResult, ScoredJob
from .prompts import SYSTEM, score_prompt

client = Anthropic()
MODEL = "claude-sonnet-4-6"


def score_job(job: Job, resume: str) -> ScoredJob:
    response = client.messages.parse(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM,
        messages=[{"role": "user", "content": score_prompt(job, resume)}],
        output_format=ScoreResult,
    )
    if response.parsed_output is None:
        raise ValueError(f"Scoring failed (stop_reason={response.stop_reason})")
    return ScoredJob(job=job, score=response.parsed_output)
