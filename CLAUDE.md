# job-radar

AI-powered job search agent that scores, ranks, and tracks job listings against a user's resume and career context — built with Claude.

## Project Goals

- **Phase 1 (Personal):** CLI/agent that auto-fetches jobs, scores them against a resume using Claude, generates tailored cover letters, and tracks application status. (Complete.)
- **Phase 2 (SaaS):** Multi-user Next.js web app with Clerk auth and per-user job pipelines. (Built — FastAPI + Next.js + Clerk. Backend is deployed on Railway; frontend is still local-dev only, pointed at the deployed backend.)

## Core Concept

Inspired by a "think like a recruiter" prompt approach:
- Takes resume + user context (skills, goals, gaps, preferences)
- Fetches fresh job listings from configured sources, or accepts a manually pasted job description (`/jobs/new`)
- Uses Claude to score each job (ATS fit 0–100, interview probability %, salary estimate, missing ATS keywords)
- Ranks and explains results, suggests resume tweaks, can rewrite/tailor the resume for one specific job, drafts cover letters
- Tracks application status over time

## Tech Stack

- **AI:** Claude API (`claude-sonnet-4-6`) via Anthropic SDK, with prompt caching on the resume block during batch scoring runs
- **Backend/Agent:** Python — CLI (`main.py`) and FastAPI (`api/`)
- **Frontend (Phase 2):** Next.js App Router (`web/`), Clerk auth
- **Database:** SQLite locally, PostgreSQL-ready via `DATABASE_URL` (target: Neon)
- **Deployment:** FastAPI is live on Railway (auto-deploys from GitHub on every push to `master`; build+deploy takes a minute or two — if a just-pushed backend change "isn't working," check the Railway deploy actually finished before assuming a code bug). Frontend → Vercel (planned, not yet deployed). Local dev frontend (`web/.env.local`'s `NEXT_PUBLIC_API_URL`) points at the deployed Railway backend, not a local one — there's no local FastAPI instance unless you start one yourself.
- **Job Sources:** We Work Remotely (RSS), Remotive (API), Indeed (via Apify). LinkedIn is never scraped — see Key Decisions.

## Project Structure

```
job-radar/
├── agent/          # Core AI agent logic — scoring, cover letters, resume rewrite, optimizer, interview prep
├── api/            # FastAPI layer — Clerk auth, REST routes for the Phase 2 frontend
├── db/             # SQLAlchemy models, session/init
├── scrapers/       # Job board fetchers (wwr, remotive, indeed — never LinkedIn)
├── tracker/        # Application pipeline commands
├── data/           # Resume, context files, job cache
├── web/            # Next.js frontend (Phase 2)
└── CLAUDE.md
```

## Key Decisions

- Phase 1 is personal-use first — get the scoring/ranking logic right before adding UI or multi-user complexity.
- Claude does the analysis; scraping/fetching is separate from AI logic so each can be swapped independently.
- Application tracking is built in from day one, not bolted on later.
- **LinkedIn is never scraped, full stop** — zero tolerance for unofficial APIs or any technique that risks account suspension. The supported path for LinkedIn (or any job site) is the manual JD-paste flow (`/jobs/new` in the web app): paste the job description and it's scored and tracked exactly like a fetched job — ATS keyword gaps included, with an option to generate a resume tailored to that job.
- **Never hard-delete user-generated data** — "deleting" a scored job from the dashboard flags it (`JobScore.is_deleted`/`deleted_at`) instead of removing the row. Phase 2 will meter SaaS billing on generation counts (scores, cover letters, tailored resumes, interview preps); a real delete would let a paid user regenerate for free indefinitely.
- **Resume versioning, no fallback files** — each user can save many resume versions (`ResumeVersion`, saved via the Profile page); exactly one is `is_active` at a time, and that's the only source the API uses for scoring/cover-letter/prep/rewrite. Saving a new version activates it immediately but never erases history — old versions stay browsable and can be reactivated. There is no shared `data/resume.md` fallback in that path (a previous version had one, and it leaked the owner's personal resume to any other signed-up user with none on file). `data/resume.md` is read directly only by the Phase 1 CLI (`main.py`), which is single-user by design.

## Owner

Rohit Nikam — building for personal job search first, SaaS second.
