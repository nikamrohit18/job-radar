'use client'
import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { useToast } from '@/components/toast'
import type { JobOut, CoverLetterOut, PrepOut, ResumeRewriteOut } from '@/lib/api'

type Tab = 'score' | 'coverletter' | 'prep' | 'resume'

function scoreColor(n: number) {
  if (n >= 70) return 'text-green-400'
  if (n >= 50) return 'text-yellow-400'
  return 'text-red-400'
}

export function JobDetailClient({ job, token: initialToken }: { job: JobOut; token: string }) {
  const { getToken } = useAuth()
  const router = useRouter()
  const toast = useToast()
  const [tab, setTab] = useState<Tab>('score')
  const [applying, setApplying] = useState(false)
  const [applied, setApplied] = useState(false)
  const [coverLetter, setCoverLetter] = useState<CoverLetterOut | null>(null)
  const [prep, setPrep] = useState<PrepOut | null>(null)
  const [tailoredResume, setTailoredResume] = useState<ResumeRewriteOut | null>(null)
  const [loading, setLoading] = useState(false)

  async function tok() {
    return (await getToken()) ?? initialToken
  }

  async function handleApply() {
    setApplying(true)
    try {
      await api.applications.apply(await tok(), job.id, {})
      setApplied(true)
      toast.success('Marked as applied.')
      router.refresh()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Failed to apply')
    } finally {
      setApplying(false)
    }
  }

  async function loadCoverLetter(regen = false) {
    setLoading(true)
    try {
      const cl = await api.coverLetter.generate(await tok(), job.id, { tone: 'professional', regen })
      setCoverLetter(cl)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Failed to generate')
    } finally {
      setLoading(false)
    }
  }

  async function loadPrep(regen = false) {
    setLoading(true)
    try {
      const p = await api.prep.generate(await tok(), job.id, regen)
      setPrep(p)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Failed to generate')
    } finally {
      setLoading(false)
    }
  }

  async function loadTailoredResume(regen = false) {
    setLoading(true)
    try {
      const r = await api.resumeRewrite.generate(await tok(), job.id, regen)
      setTailoredResume(r)
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Failed to generate')
    } finally {
      setLoading(false)
    }
  }

  const tabBtn = (t: Tab, label: string) => (
    <button
      key={t}
      onClick={() => setTab(t)}
      className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
        tab === t ? 'border-indigo-500 text-white' : 'border-transparent text-gray-400 hover:text-white'
      }`}
    >
      {label}
    </button>
  )

  const s = job.score

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-white">{job.title}</h1>
            <p className="text-gray-400 mt-1">{job.company} · {job.location ?? 'Remote'}</p>
            {job.url && (
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-indigo-400 hover:text-indigo-300 mt-1 inline-block"
              >
                View listing →
              </a>
            )}
          </div>
          <button
            onClick={handleApply}
            disabled={applying || applied}
            className="px-5 py-2 bg-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
          >
            {applied ? 'Applied ✓' : applying ? 'Saving…' : 'Mark as Applied'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-800 mb-6 -mx-4 px-4">
        {tabBtn('score', 'Score')}
        {tabBtn('coverletter', 'Cover Letter')}
        {tabBtn('prep', 'Interview Prep')}
        {tabBtn('resume', 'Tailored Resume')}
      </div>

      {/* Score tab */}
      {tab === 'score' && (
        s ? (
          <div className="space-y-6">
            <div className="grid grid-cols-3 gap-4">
              {[
                { value: `${s.ats_score}`, label: 'ATS Score / 100', color: scoreColor(s.ats_score) },
                { value: `${s.interview_probability}%`, label: 'Interview Probability', color: 'text-indigo-400' },
                { value: `$${s.salary_min.toLocaleString('en-US')}–${s.salary_max.toLocaleString('en-US')}`, label: 'Est. Salary (USD)', color: 'text-gray-300' },
              ].map(({ value, label, color }) => (
                <div key={label} className="bg-gray-900 border border-gray-800 rounded-lg p-4 text-center">
                  <p className={`text-2xl font-bold ${color}`}>{value}</p>
                  <p className="text-xs text-gray-500 mt-1">{label}</p>
                </div>
              ))}
            </div>

            <p className="text-gray-300 text-sm leading-relaxed">{s.summary}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                { title: 'Strengths', items: s.strengths, color: 'text-green-400', marker: '+' },
                { title: 'Gaps', items: s.gaps, color: 'text-red-400', marker: '–' },
                { title: 'Missing Keywords', items: s.missing_keywords, color: 'text-orange-400', marker: '#' },
                { title: 'Resume Tweaks', items: s.resume_tweaks, color: 'text-yellow-400', marker: '*' },
              ].map(({ title, items, color, marker }) => (
                <div key={title}>
                  <h3 className={`text-xs font-semibold ${color} uppercase tracking-wide mb-2`}>{title}</h3>
                  <ul className="space-y-1.5">
                    {items.map((item, i) => (
                      <li key={i} className="text-sm text-gray-300 flex gap-2">
                        <span className={`${color} shrink-0`}>{marker}</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No score data for this job.</p>
        )
      )}

      {/* Cover Letter tab */}
      {tab === 'coverletter' && (
        !coverLetter ? (
          <div className="text-center py-16">
            <p className="text-gray-400 mb-4 text-sm">Generate a tailored cover letter for this role.</p>
            <button
              onClick={() => loadCoverLetter()}
              disabled={loading}
              className="px-6 py-3 bg-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Generating…' : 'Generate Cover Letter'}
            </button>
          </div>
        ) : (
          <div>
            <div className="flex justify-between items-center mb-4">
              <span className="text-xs text-gray-500">
                Tone: {coverLetter.tone}{coverLetter.cached ? ' · cached' : ''}
              </span>
              <button
                onClick={() => loadCoverLetter(true)}
                disabled={loading}
                className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-50"
              >
                {loading ? 'Regenerating…' : 'Regenerate'}
              </button>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <pre className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed font-sans">
                {coverLetter.content}
              </pre>
            </div>
          </div>
        )
      )}

      {/* Interview Prep tab */}
      {tab === 'prep' && (
        !prep ? (
          <div className="text-center py-16">
            <p className="text-gray-400 mb-4 text-sm">Generate an interview prep guide tailored to this role and your gaps.</p>
            <button
              onClick={() => loadPrep()}
              disabled={loading}
              className="px-6 py-3 bg-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Generating…' : 'Generate Prep Guide'}
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex justify-end">
              <button
                onClick={() => loadPrep(true)}
                disabled={loading}
                className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-50"
              >
                {loading ? 'Regenerating…' : 'Regenerate'}
              </button>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Company Snapshot</h3>
              <p className="text-sm text-gray-300">{prep.company_snapshot}</p>
            </div>

            <div>
              <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wide mb-2">Key Themes</h3>
              <ul className="space-y-1">
                {prep.key_themes.map((t, i) => (
                  <li key={i} className="text-sm text-gray-300 flex gap-2">
                    <span className="text-indigo-400 shrink-0">*</span>{t}
                  </li>
                ))}
              </ul>
            </div>

            {[
              { title: 'Technical Questions', items: prep.technical_questions },
              { title: 'Behavioral Questions', items: prep.behavioral_questions },
            ].map(({ title, items }) => (
              <div key={title}>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">{title}</h3>
                <div className="space-y-3">
                  {items.map((q, i) => (
                    <div key={i} className="bg-gray-900 border border-gray-800 rounded-lg p-4">
                      <p className="text-sm font-medium text-white mb-2">{q.question}</p>
                      <p className="text-sm text-gray-400">{q.talking_point}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {prep.gap_questions.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-yellow-400 uppercase tracking-wide mb-3">
                  Gap / Tough Questions
                </h3>
                <div className="space-y-3">
                  {prep.gap_questions.map((q, i) => (
                    <div key={i} className="bg-gray-900 border border-yellow-900/30 rounded-lg p-4">
                      <p className="text-xs text-yellow-500 mb-1">Gap: {q.gap}</p>
                      <p className="text-sm font-medium text-white mb-2">&quot;{q.question}&quot;</p>
                      <p className="text-sm text-gray-400">{q.talking_point}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      )}

      {/* Tailored Resume tab */}
      {tab === 'resume' && (
        !tailoredResume ? (
          <div className="text-center py-16">
            <p className="text-gray-400 mb-4 text-sm">
              Rewrite your resume to fit this role, targeting its gaps and missing ATS keywords.
            </p>
            <button
              onClick={() => loadTailoredResume()}
              disabled={loading}
              className="px-6 py-3 bg-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Generating…' : 'Generate Tailored Resume'}
            </button>
          </div>
        ) : (
          <div>
            <div className="flex justify-between items-center mb-4">
              <span className="text-xs text-gray-500">
                {tailoredResume.cached ? 'Cached' : 'Freshly generated'}
              </span>
              <button
                onClick={() => loadTailoredResume(true)}
                disabled={loading}
                className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-50"
              >
                {loading ? 'Regenerating…' : 'Regenerate'}
              </button>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <pre className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed font-sans">
                {tailoredResume.content}
              </pre>
            </div>
          </div>
        )
      )}
    </div>
  )
}
