"""
Interview prep generator.
Produces role-specific questions, company research, and gap-probing questions
from the job description and scored gaps. Uses messages.parse() for structured output.
"""

from anthropic import Anthropic
from pydantic import BaseModel

from .models import Job

client = Anthropic()
MODEL = "claude-sonnet-4-6"


class InterviewQuestion(BaseModel):
    question: str        # Phrased as a real interviewer would ask it
    talking_point: str   # Which resume achievement to cite; include specific numbers


class GapQuestion(BaseModel):
    question: str        # The tough probing question
    gap: str             # One line: what gap is being tested
    talking_point: str   # How to answer honestly without over-explaining


class PrepResult(BaseModel):
    company_snapshot: str                          # 3-4 sentences from JD signals
    key_themes: list[str]                          # 3-5 short phrases: thread through every answer
    technical_questions: list[InterviewQuestion]   # 5-6 role-specific technical questions
    behavioral_questions: list[InterviewQuestion]  # 4-5 behavioral/leadership questions
    gap_questions: list[GapQuestion]               # 2-4 tough questions tied to scored gaps


SYSTEM = """You prepare senior technology executives for job interviews. Your output is a prep guide they will read the night before the interview.

Rules:

1. No em-dashes. Not one. Use commas, full stops, or rewrite.
2. No buzzwords: leverage, utilize, spearhead, champion, synergy, robust, transformative, cutting-edge, innovative, dynamic, passionate, thrilled, holistic, proactive, thought leader, paradigm, impactful, actionable.
3. Questions must sound like a real interviewer at this specific company, not a textbook. No "Tell me about yourself." No generic openers.
4. Talking points must cite specific achievements from the resume: named projects, real numbers, actual technologies. No vague claims.
5. Gap questions must be honest. Name the real weakness the interviewer will probe. Do not soften it into a non-answer.
6. key_themes: short phrases only, 4-8 words each. These are the threads the candidate should weave into every answer regardless of what is asked.
7. company_snapshot: draw only from signals in the job description -- what the company actually does, the problem space, culture signals from the language they use in the JD. Do not invent facts."""


def generate(job: Job, resume: str, gaps: list[str] | None = None) -> PrepResult:
    """
    Generate a structured interview prep guide for a specific job.
    gaps: list of gap strings from JobScore.gaps, used to generate tough probing questions.
    """
    gap_block = ""
    if gaps:
        gap_items = "\n".join(f"- {g}" for g in gaps)
        gap_block = f"""
GAPS IDENTIFIED BY SCORING (areas the interviewer will likely probe):
{gap_items}
"""

    prompt = f"""Prepare the candidate for an interview at {job.company} for the role: {job.title}.

RESUME:
{resume}

JOB DESCRIPTION:
{job.description}
{gap_block}
Instructions:
- company_snapshot: 3-4 sentences. Pull only from what the JD reveals about the company, the team, and what they care about. No invented facts.
- key_themes: 3-5 short phrases the candidate should thread through every answer. Pull from where the resume and JD align most strongly.
- technical_questions: 5-6 questions specific to the technologies, domains, and responsibilities named in this JD. Phrased as the interviewer would actually ask them, not as textbook prompts.
- behavioral_questions: 4-5 questions that probe for leadership, delivery under pressure, cross-functional influence, or team building -- whichever ones this specific role and company are most likely to focus on.
- gap_questions: one question per gap listed above. For each: state the gap plainly in "gap", write the question as the interviewer would phrase it, then write a talking point that helps the candidate answer honestly without over-explaining or apologising."""

    response = client.messages.parse(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_format=PrepResult,
    )

    if response.parsed_output is None:
        raise ValueError(f"Interview prep generation failed (stop_reason={response.stop_reason})")

    return response.parsed_output
