# job-radar

AI-powered job search agent that scores, ranks, and tracks job listings against a user's resume and career context — built with Claude.

## Project Goals

- **Phase 1 (Personal):** CLI/agent that auto-fetches jobs, scores them against a resume using Claude, generates tailored cover letters, and tracks application status.
- **Phase 2 (SaaS):** Multi-user Next.js web app with auth, billing, and per-user job pipelines.

## Core Concept

Inspired by a "think like a recruiter" prompt approach:
- Takes resume + user context (skills, goals, gaps, preferences)
- Fetches fresh job listings from configured sources
- Uses Claude to score each job (ATS fit 0–100, interview probability %, salary estimate)
- Ranks and explains results, suggests resume tweaks, drafts cover letters
- Tracks application status over time

## Tech Stack (Planned)

- **AI:** Claude API (`claude-sonnet-4-6`) via Anthropic SDK
- **Backend/Agent:** Python (FastAPI or CLI)
- **Frontend (Phase 2):** Next.js App Router
- **Database:** PostgreSQL
- **Auth (Phase 2):** Clerk
- **Deployment:** Vercel
- **Job Sources:** LinkedIn, Indeed, Wellfound (to be confirmed)

## Project Structure (To Be Built)

```
job-radar/
├── agent/          # Core AI agent logic
├── scrapers/       # Job board fetchers
├── data/           # Resume, context files, job cache
├── web/            # Next.js frontend (Phase 2)
└── CLAUDE.md
```

## Key Decisions

- Phase 1 is personal-use first — get the scoring/ranking logic right before adding UI or multi-user complexity.
- Claude does the analysis; scraping/fetching is separate from AI logic so each can be swapped independently.
- Application tracking is built in from day one, not bolted on later.

## Owner

Rohit Nikam — building for personal job search first, SaaS second.
