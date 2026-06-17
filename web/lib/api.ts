const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export type ScoreOut = {
  ats_score: number
  interview_probability: number
  salary_min: number
  salary_max: number
  strengths: string[]
  gaps: string[]
  missing_keywords: string[]
  resume_tweaks: string[]
  summary: string
  scored_at: string
}

export type JobOut = {
  id: number
  title: string
  company: string
  location: string | null
  url: string | null
  source: string | null
  date_posted: string | null
  created_at: string
  score: ScoreOut | null
}

export type FetchOut = {
  fetched: number
  new: number
  skipped: number
  jobs: JobOut[]
}

export type ApplicationOut = {
  id: number
  job_id: number
  status: string
  notes: string | null
  applied_at: string | null
  updated_at: string
  job: JobOut | null
  score: ScoreOut | null
}

export type PipelineOut = {
  applied: ApplicationOut[]
  screening: ApplicationOut[]
  interview: ApplicationOut[]
  offer: ApplicationOut[]
  rejected: ApplicationOut[]
  withdrawn: ApplicationOut[]
}

export type CoverLetterOut = {
  id: number
  content: string
  tone: string
  generated_at: string
  cached: boolean
}

export type ResumeRewriteOut = {
  id: number
  content: string
  generated_at: string
  cached: boolean
}

export type PrepQuestionOut = { question: string; talking_point: string }
export type PrepGapQuestionOut = { gap: string; question: string; talking_point: string }

export type PrepOut = {
  id: number
  job_id: number
  company_snapshot: string
  key_themes: string[]
  technical_questions: PrepQuestionOut[]
  behavioral_questions: PrepQuestionOut[]
  gap_questions: PrepGapQuestionOut[]
  generated_at: string
  cached: boolean
}

export type UserOut = {
  id: number
  clerk_id: string | null
  email: string | null
  name: string | null
  has_resume: boolean
  created_at: string
}

async function apiFetch<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
    cache: 'no-store',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `API error ${res.status}`)
  }
  return res.json()
}

export const api = {
  jobs: {
    list: (token: string, limit = 30) =>
      apiFetch<JobOut[]>(`/jobs?limit=${limit}`, token),
    get: (token: string, id: number) =>
      apiFetch<JobOut>(`/jobs/${id}`, token),
    fetch: (token: string, body: { source: string; query: string; location: string; days: number; limit: number }) =>
      apiFetch<FetchOut>('/jobs/fetch', token, { method: 'POST', body: JSON.stringify(body) }),
    createManual: (token: string, body: { jd_text: string; title: string; company: string; location?: string; url?: string }) =>
      apiFetch<JobOut>('/jobs/manual', token, { method: 'POST', body: JSON.stringify(body) }),
  },
  applications: {
    pipeline: (token: string) =>
      apiFetch<PipelineOut>('/applications/pipeline', token),
    apply: (token: string, jobId: number, body: { note?: string; date?: string }) =>
      apiFetch<ApplicationOut>(`/applications/${jobId}/apply`, token, {
        method: 'POST', body: JSON.stringify(body),
      }),
    updateStatus: (token: string, jobId: number, newStatus: string) =>
      apiFetch<ApplicationOut>(`/applications/${jobId}/status`, token, {
        method: 'PUT', body: JSON.stringify({ new_status: newStatus }),
      }),
    addNote: (token: string, jobId: number, text: string) =>
      apiFetch<ApplicationOut>(`/applications/${jobId}/note`, token, {
        method: 'POST', body: JSON.stringify({ text }),
      }),
  },
  coverLetter: {
    generate: (token: string, jobId: number, body: { tone: string; regen?: boolean }) =>
      apiFetch<CoverLetterOut>(`/jobs/${jobId}/coverletter`, token, {
        method: 'POST', body: JSON.stringify(body),
      }),
  },
  prep: {
    generate: (token: string, jobId: number, regen = false) =>
      apiFetch<PrepOut>(`/jobs/${jobId}/prep`, token, {
        method: 'POST', body: JSON.stringify({ regen }),
      }),
  },
  resumeRewrite: {
    generate: (token: string, jobId: number, regen = false) =>
      apiFetch<ResumeRewriteOut>(`/jobs/${jobId}/resume`, token, {
        method: 'POST', body: JSON.stringify({ regen }),
      }),
  },
  users: {
    me: (token: string) => apiFetch<UserOut>('/users/me', token),
    updateResume: (token: string, content: string) =>
      apiFetch<UserOut>('/users/me/resume', token, {
        method: 'PUT', body: JSON.stringify({ content }),
      }),
  },
}
