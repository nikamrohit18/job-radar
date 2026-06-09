# job-radar

> AI-powered job search agent — scores job listings against your resume, ranks them by fit, generates tailored cover letters, tracks your pipeline, and preps you for interviews.

[![CI](https://github.com/nikamrohit18/job-radar/actions/workflows/ci.yml/badge.svg)](https://github.com/nikamrohit18/job-radar/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Claude](https://img.shields.io/badge/claude-sonnet--4--6-8A2BE2)
![Phase](https://img.shields.io/badge/phase-1%20%E2%80%94%20CLI-green)

---

## What it does

Most job search tools match keywords. job-radar thinks like a recruiter.

It reads your resume, fetches fresh listings from job boards, and uses Claude to score each role on ATS fit (0–100), interview probability, and estimated salary. It explains exactly where you match, where you fall short, and what to fix. Then it writes the cover letter, preps your interview questions, and tracks every application through your pipeline.

---

## Features

| Feature | Command | Description |
|---|---|---|
| Fetch & score | `fetch` | Pull listings from WWR / Remotive, score each against your resume |
| Ranked results | `list` | Top scored jobs from the database, sorted by ATS fit |
| Cover letters | `coverletter` | Three tones: professional, startup, brief — sounds human, not AI |
| Application tracker | `apply` / `status` / `note` / `pipeline` | Full pipeline from applied to offer |
| Resume optimizer | `optimize` | Aggregates gaps across all scored jobs, ranks universal improvements |
| Interview prep | `prep` | Role-specific questions, company snapshot, gap-probing tough questions |

---

## Tech stack

- **AI** — [Claude](https://anthropic.com) (`claude-sonnet-4-6`) via Anthropic SDK — structured output (`messages.parse`) for scoring, free-form (`messages.create`) for cover letters
- **Backend** — Python 3.11, SQLAlchemy ORM, Pydantic v2
- **Database** — SQLite (local) → PostgreSQL-ready via `DATABASE_URL`
- **Job sources** — We Work Remotely (RSS, free), Remotive (API, free), Indeed (via Apify)
- **SaaS-ready** — `user_id` foreign key on every table from day one

---

## Quick start

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### Install

**In PowerShell, from the project root (`D:\Development Projects\job-radar`):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configure

**In PowerShell, from the project root:**

```powershell
Copy-Item .env.example .env
notepad .env
```

Set at minimum:

```env
ANTHROPIC_API_KEY=your_key_here
USER_EMAIL=you@example.com
USER_NAME=Your Name
```

### Smoke test

**In PowerShell, from the project root:**

```powershell
python main.py sample
```

Scores the bundled sample job against your resume. No DB write, no job board call — confirms Claude is wired up correctly.

<details>
<summary>Example output</summary>

```
============================================================
  #0  Head of AI & Data Transformation @ Regional Insurance Group (APAC)
============================================================
  ATS Score:             91/100
  Interview Probability: 82%
  Salary Estimate:       $180,000 – $240,000

  Strong match across AI/ML delivery, insurance domain, and APAC executive
  leadership. Resume demonstrates measurable ROI and the right technology stack.

  Strengths:
    + XGBoost/LightGBM claims triage with 40% processing reduction
    + GNN-based fraud detection cutting false positives from 60% to 18%
    + $6M+ revenue impact across AI and data programs
    + 200+ workload cloud migration with zero downtime

  Gaps:
    - TOGAF certification not listed
    - Explicit enterprise architecture governance language missing
    - MLOps platform ownership not named directly

  Resume Tweaks:
    * Add 'enterprise architecture' and 'TOGAF' to skills section
    * Quantify cloud cost savings from the migration program
    * Name the MLOps toolchain (MLflow, SageMaker Pipelines) explicitly
```

</details>

---

## Usage

### Fetch and score jobs

**In PowerShell, from the project root:**

```powershell
python main.py fetch -q "head of AI" -s wwr
python main.py fetch -q "principal AI architect" -s remotive
```

Fetches listings, deduplicates against the database, scores each new job, and prints a ranked summary.

```
Fetching from wwr: query='head of AI' | location='remote'
  18 listings retrieved
  5 new  |  13 already in DB
Scoring: VP of AI Engineering @ Acme Corp...
Scoring: Head of AI Transformation @ RegionalBank...
...
============================================================
  5 JOBS SCORED -- ranked by ATS fit
============================================================
  #12  VP of AI Engineering @ Acme Corp
  ATS Score:   87/100  |  Interview: 74%  |  $190,000 – $250,000

  #9   Head of AI Transformation @ RegionalBank
  ATS Score:   81/100  |  Interview: 69%  |  $160,000 – $200,000
```

### View ranked results

```powershell
python main.py list
python main.py list -n 10
```

### Track applications

```powershell
# Start tracking a job
python main.py apply 9

# Move through the pipeline
python main.py status 9 screening
python main.py status 9 interview

# Add notes
python main.py note 9 "Call with hiring manager Thursday 3pm BKK time"

# View full pipeline
python main.py pipeline
```

<details>
<summary>Pipeline output</summary>

```
============================================================
  APPLICATION PIPELINE  --  2 active  |  0 offer  |  1 closed
============================================================

  * INTERVIEW (1)  -----------------------------------
    #9  Head of AI Transformation @ RegionalBank
        2 days ago  |  ATS 81/100
        > [2026-06-09] screening -> interview

  * APPLIED (1)  -------------------------------------
    #12  VP of AI Engineering @ Acme Corp
        8 days ago  |  ATS 87/100  ! follow up
        > [2026-06-01] Applied

  * REJECTED (1)  ------------------------------------
    #3  Senior ML Engineer @ StartupCo
        5 days ago  |  ATS 52/100
        > [2026-06-04] applied -> rejected
```

</details>

### Generate a cover letter

```powershell
python main.py coverletter 9
python main.py coverletter 9 --tone startup
python main.py coverletter 9 --tone brief --save
python main.py coverletter 9 --regen        # force regenerate
```

Three tones: `professional` (default), `startup`, `brief`. Cached in the database — regenerates only when `--regen` is passed. Saved to `covers/` when `--save` is passed.

The prompt has hard rules against em-dashes, rhetorical contrasts, abstract industry openers, AI buzzwords, and hollow closings. Output is plain text, ready to paste into an email.

### Optimize your resume

```powershell
python main.py optimize
python main.py optimize --min-jobs 1    # run with fewer scored jobs
python main.py optimize --save          # save to optimizations/
```

Reads all `resume_tweaks` from every scored job, sends them to Claude, and gets back a ranked list of universal improvements — suggestions that appeared across multiple roles, not one-off job-specific gaps.

<details>
<summary>Example output</summary>

```
============================================================
  RESUME OPTIMIZER  --  8 jobs analyzed
============================================================

  Assessment:
  Strong on measurable delivery outcomes and domain depth.
  Main recurring gap is vocabulary mismatch: the work covers event-driven systems
  and LLM orchestration, but the resume does not use those exact phrases.

  TOP 6 IMPROVEMENTS  --  ranked by expected impact

  1. [skills] Add 'event-driven architecture' and 'async job pipeline' to the skills section
     Flagged by 6/8 jobs
     > ATS parsers scan for exact-match tool names. The underlying work exists
       but is not labeled with the terms recruiters search for.

  2. [summary] Rewrite the opening line to lead with the $6M revenue impact figure
     Flagged by 5/8 jobs
     > Recruiters spend 7 seconds on the summary. A concrete number in the
       first line is the single highest-leverage change available.

  3. [skills] Add 'LLM orchestration' and 'structured data extraction' as explicit keywords
     Flagged by 5/8 jobs
     > Current shortlist terms for senior AI roles. The work exists in personal
       projects and at prior employers but the resume does not use this phrasing.
```

</details>

### Interview prep

```powershell
python main.py prep 9
python main.py prep 9 --save            # save to prep/
python main.py prep 9 --regen           # force regenerate
```

Generates a full prep guide: company snapshot from JD signals, 3–5 key themes to thread through every answer, 5–6 technical questions, 4–5 behavioral questions, and a gap section — tough questions the interviewer will use to probe your scored weaknesses, each with a specific talking point drawn from your resume.

<details>
<summary>Example output (excerpt)</summary>

```
============================================================
  INTERVIEW PREP  --  #9  Head of AI Transformation @ RegionalBank
============================================================

  COMPANY SNAPSHOT
  RegionalBank is a mid-sized financial institution expanding its AI capability
  across retail and commercial banking. The JD signals a team building from
  near-zero ML maturity, with board-level sponsorship and a mandate to deliver
  production systems within 12 months, not a strategy document.

  KEY THEMES  --  thread these through every answer
    * shipped production AI systems with measurable outcomes
    * enterprise delivery under regulatory constraints
    * end-to-end ownership from architecture to deployment
    * APAC domain expertise

  ------------------------------------------------------------
  TECHNICAL QUESTIONS (5)
  ------------------------------------------------------------

  1. Walk me through the architecture of your claims triage model. How did you
     handle model risk sign-off in a regulated environment?
     > Reference the XGBoost pipeline at Falcon Insurance: trained on 3 years of
       claims data, 40% processing reduction, deployed on SageMaker with MLflow
       experiment tracking. Describe the model risk framework you built to satisfy
       compliance sign-off — that is exactly what a bank needs to hear.

  ------------------------------------------------------------
  GAP / TOUGH QUESTIONS (3)
  ------------------------------------------------------------

  1. Gap: TOGAF certification not listed
     Q: "How do you approach enterprise architecture governance without a formal EA background?"
     > Frame around outcomes: the platforms you have built are enterprise-scale
       by any definition. Acknowledge the gap is the certification, not the practice.
       Name one specific EA governance pattern you applied on a past program.
```

</details>

---

## Project structure

```
job-radar/
├── agent/
│   ├── scorer.py          # Claude scoring — ATS fit, interview probability, salary
│   ├── cover_letter.py    # Cover letter generator — three tones, human writing rules
│   ├── optimizer.py       # Resume optimizer — universal gap analysis across scored jobs
│   ├── interview_prep.py  # Interview prep — questions, company snapshot, gap probing
│   └── models.py          # Pydantic models shared across agent modules
├── db/
│   ├── models.py          # SQLAlchemy ORM — User, Job, JobScore, Application, CoverLetter, InterviewPrep
│   └── session.py         # DB init, session factory, default user bootstrap
├── scrapers/
│   ├── wwr.py             # We Work Remotely — RSS, free, default source
│   ├── remotive.py        # Remotive — JSON API, free
│   └── indeed.py          # Indeed — placeholder, requires Apify for production use
├── tracker/
│   └── commands.py        # Application tracker — apply, status, note, pipeline
├── data/
│   ├── resume.md          # Your resume (Markdown, loaded at runtime)
│   └── sample_job.json    # Bundled sample job for smoke testing
├── main.py                # CLI entry point — all commands wired here
├── .env.example           # Environment variable template
└── requirements.txt
```

---

## Roadmap

### Phase 1 — CLI (current)

- [x] Job fetching — WWR, Remotive, Indeed stub
- [x] Claude scoring — ATS fit, interview probability, salary estimate, strengths/gaps/tweaks
- [x] Application tracker — full pipeline with follow-up flags
- [x] Cover letter generator — three tones, human writing hard rules
- [x] Resume optimizer — universal gap analysis across all scored jobs
- [x] Interview prep — role-specific questions, company research, gap probing
- [ ] HN Who's Hiring parser
- [ ] Wellfound integration
- [ ] Apify integration for Indeed / LinkedIn jobs (within rate limits)

### Phase 2 — SaaS

- [ ] Next.js App Router frontend
- [ ] FastAPI backend
- [ ] Clerk authentication
- [ ] PostgreSQL (schema is already multi-tenant — `user_id` on every table)
- [ ] Vercel deployment
- [ ] Per-user job pipelines and resume management

---

## Configuration reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key |
| `DATABASE_URL` | No | `sqlite:///./job_radar.db` | SQLite locally, swap to PostgreSQL for production |
| `USER_EMAIL` | Yes | — | Your email — used to create the default Phase 1 user |
| `USER_NAME` | No | — | Your display name |
| `JOB_SOURCE` | No | `wwr` | Default job source: `wwr`, `remotive`, `indeed` |
| `INDEED_QUERY` | No | — | Default search query (overridable with `--query`) |
| `INDEED_LOCATION` | No | `remote` | Default location (overridable with `--location`) |
| `INDEED_DAYS_OLD` | No | `3` | How many days back to search (overridable with `--days`) |

---

## Job sources

| Source | Flag | Cost | Notes |
|---|---|---|---|
| We Work Remotely | `--source wwr` | Free | RSS feed, remote-only, 25+ tech jobs/fetch. **Default.** |
| Remotive | `--source remotive` | Free | JSON API, remote-only, good for engineering roles |
| Indeed | `--source indeed` | Apify required | Direct scraping is 403-blocked. Use [Apify Indeed scraper](https://apify.com/misceres/indeed-scraper) |
| LinkedIn | — | — | Direct scraping violates LinkedIn ToS and risks account ban. Use Phantombuster or Apify within their rate limits, or the manual `apply` command to track roles you find manually |

---

Built by [Rohit Nikam](https://rohitnikam.tech) — personal use first, SaaS second.
