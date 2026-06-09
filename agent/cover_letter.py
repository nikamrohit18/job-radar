"""
Cover letter generator.
Uses messages.create() (not parse) — output is free-form text.
"""

from anthropic import Anthropic
from .models import Job

client = Anthropic()
MODEL = "claude-sonnet-4-6"

TONES = {
    "professional": (
        "Calm, clear, and senior. Written for a large corporate, insurer, or multinational "
        "where measured confidence carries more weight than energy."
    ),
    "startup": (
        "Direct and concrete. Written for a scale-up or founder-led company. "
        "Short sentences. Show that you build things, not just lead them."
    ),
    "brief": (
        "Two paragraphs, under 180 words. Every word earns its place. "
        "Written for senior roles where the CV does the heavy lifting."
    ),
}

SYSTEM = """You write cover letters for senior technology executives. Your only job is to make the letter sound like a real person wrote it.

HARD RULES — break any of these and the letter is rejected:

1. No em-dashes. Not one. Replace every -- or — with a comma, a full stop, or rewrite the sentence.

2. No rhetorical contrasts. These patterns are instant AI tells — never use them:
   - "X is not the same as Y"
   - "X is not a strategy exercise, it's an execution problem"
   - "X doesn't respond to Y, it responds to Z"
   - "The gap between X and Y is where Z happens"
   - "Not [bad thing], but [good thing]"

3. No abstract industry openers. Do not open with a philosophical observation about the sector, the market, or the nature of the role. Open with something concrete and specific — a number, a named company, a specific project, or a direct statement of what you did.

4. No AI buzzwords. These are banned: leverage, utilize, spearhead, champion, orchestrate, synergy, robust, seamless, transformative, cutting-edge, innovative, dynamic, passionate, thrilled, excited, thought leader, paradigm, ecosystem, holistic, proactive, deep expertise, proven track record, value-add, deliverable, actionable, impactful, outcomes-driven.

5. No stiff closings. These are banned: "I look forward to hearing from you", "at your earliest convenience", "please do not hesitate to contact me", "I am available at your convenience", "I welcome the opportunity to discuss".

6. No hollow openers. Never start with: "I am writing to apply", "I was excited to see", "I am reaching out regarding", "I came across this opportunity".

WRITE LIKE THIS INSTEAD:

- Open sentence: name a specific outcome, a specific company, or ask a question that only this candidate could answer. Not a sector observation.
- Use plain words. "Built" not "architected and delivered". "Cut" not "reduced by optimising". "Ran" not "oversaw the management of".
- Mix sentence lengths. One short. Then a longer one that gives the context. Then another short one.
- Contractions are fine. "I've", "I'm", "it's", "didn't", "we'd".
- Numbers without softening. "40%" not "approximately 40%". "$1.4M" not "over a million dollars".
- End with one direct sentence asking for a meeting or call. Nothing more.

BAD EXAMPLE (do not write like this):
"Building an AI function inside an insurer is not the same as advising on one from the outside. The gap between a well-designed roadmap and shipped platforms is where most programs stall — and closing that gap is precisely what I have spent the last decade doing."

GOOD EXAMPLE (write like this):
"The claims triage model I built at Falcon Insurance cut processing time by 40% and paid back its build cost seven times over in the first year. That kind of result comes from knowing both the insurance domain and the ML stack well enough to make the right tradeoffs — and from having done it before."

The second version is specific, grounded, uses no em-dash, and sounds like a person talking."""


def generate(job: Job, resume: str, tone: str = "professional") -> str:
    """Generate a tailored cover letter. Returns plain text, no markdown."""
    tone_instruction = TONES.get(tone, TONES["professional"])
    word_target = "under 180 words, 2 short paragraphs" if tone == "brief" else "260-340 words, 3-4 paragraphs"

    prompt = f"""Write a cover letter for this application.

JOB
Title: {job.title}
Company: {job.company}
Location: {job.location}

Description:
{job.description}

---

CANDIDATE RESUME
{resume}

---

REQUIREMENTS
- Length: {word_target}
- Tone: {tone_instruction}
- Paragraph 1: Open with a specific, concrete statement. Reference a real outcome from the resume that connects directly to this role. No sector observations, no philosophical statements.
- Paragraph 2 (and 3 if needed): Pick the 2-3 achievements from the resume that best match the job's stated requirements. Use the exact numbers and technology names. Do not summarise — be specific.
- Final paragraph: One sentence showing you understand {job.company}'s specific context or challenge. One sentence requesting a call or meeting. That is all.

OUTPUT
Plain text only. No markdown, no bold, no headers, no bullet points. Paragraphs separated by a blank line. Ready to paste into an email as-is."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()
