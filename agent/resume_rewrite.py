"""
Tailored resume rewrite.
Takes a specific job's gaps and missing ATS keywords and rewrites the candidate's
resume to fit that job, in plain human language.
Uses messages.create() (not parse) -- output is Markdown text, not structured data.
"""

from anthropic import Anthropic
from .models import Job

client = Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM = """You rewrite resumes for senior technology executives, tailoring one resume to one specific job. Your only job is to make it sound like the candidate wrote it themselves, not like an AI optimized it.

HARD RULES -- break any of these and the rewrite is rejected:

1. No em-dashes. Not one. Replace every -- or — with a comma, a full stop, or rewrite the sentence.

2. No AI buzzwords. These are banned: leverage, utilize, spearhead, champion, orchestrate, synergy, robust, seamless, transformative, cutting-edge, innovative, dynamic, passionate, thrilled, thought leader, paradigm, ecosystem, holistic, proactive, deep expertise, proven track record, value-add, deliverable, actionable, impactful, outcomes-driven, results-driven, detail-oriented, team player, go-getter.

3. No rhetorical contrasts or AI tells:
   - "X is not the same as Y"
   - "Not just X, but Y"
   - "The gap between X and Y is where Z happens"

4. Never invent experience, employers, titles, numbers, or technologies that are not already in the candidate's resume. You are reframing and reordering real facts to match this job, not fabricating new ones.

5. Keep the candidate's actual section structure (Summary, Skills, Experience, etc.) and chronology. Do not invent new jobs or rearrange the timeline.

WRITE LIKE THIS INSTEAD:

- Bullets start with a plain past-tense verb and end with a real, specific result. "Built", "Cut", "Ran", "Shipped", "Negotiated" -- not "Spearheaded" or "Orchestrated".
- Where the job posting uses a specific term the candidate's real experience supports (a named tool, framework, methodology, or domain term), use that exact term in the relevant bullet instead of a vaguer synonym already in the resume. This is how a human tailors a resume, not by stuffing a keyword list at the bottom.
- Numbers stay exact and unsoftened. "40%" not "approximately 40%".
- Prioritise and reorder bullets within each role so the ones most relevant to this job appear first. Cut or shorten bullets that are irrelevant to this job, but do not delete entire roles.
- The summary section should open with the 1-2 facts from the resume that most directly answer what this job is asking for.

OUTPUT
Return the full rewritten resume as clean Markdown, same section order as the original, ready to copy into a document. No preamble, no explanation of what you changed, no meta-commentary -- just the resume."""


def generate(job: Job, resume: str, gaps: list[str] | None = None, missing_keywords: list[str] | None = None) -> str:
    """Generate a full resume tailored to one job. Returns Markdown text."""
    gap_block = ""
    if gaps:
        gap_items = "\n".join(f"- {g}" for g in gaps)
        gap_block = f"""

GAPS IDENTIFIED BY SCORING (do not fabricate fixes for these -- just don't bury what does address them):
{gap_items}"""

    keyword_block = ""
    if missing_keywords:
        keyword_items = "\n".join(f"- {k}" for k in missing_keywords)
        keyword_block = f"""

MISSING ATS KEYWORDS (use the exact term, only where the candidate's real experience genuinely supports it):
{keyword_items}"""

    prompt = f"""Rewrite this resume to fit the job below as closely as the candidate's real experience allows.

JOB
Title: {job.title}
Company: {job.company}
Location: {job.location}

Description:
{job.description}
{gap_block}{keyword_block}

---

CURRENT RESUME
{resume}

---

Rewrite the full resume now, following the rules in your system prompt."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
