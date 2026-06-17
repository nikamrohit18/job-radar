'use client'
import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

export function JdPasteForm({ token: initialToken }: { token: string }) {
  const { getToken } = useAuth()
  const router = useRouter()

  const [title, setTitle] = useState('')
  const [company, setCompany] = useState('')
  const [location, setLocation] = useState('')
  const [url, setUrl] = useState('')
  const [jdText, setJdText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = title.trim() && company.trim() && jdText.trim() && !submitting

  async function handleSubmit() {
    if (!canSubmit) return
    setSubmitting(true)
    setError(null)
    try {
      const token = (await getToken()) ?? initialToken
      const job = await api.jobs.createManual(token, {
        jd_text: jdText.trim(),
        title: title.trim(),
        company: company.trim(),
        location: location.trim(),
        url: url.trim(),
      })
      router.push(`/jobs/${job.id}`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to analyze job description')
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium text-gray-400 block mb-1.5">Job title *</label>
          <input
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="e.g. Head of AI"
            className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-400 block mb-1.5">Company *</label>
          <input
            value={company}
            onChange={e => setCompany(e.target.value)}
            placeholder="e.g. Acme Insurance"
            className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-400 block mb-1.5">Location (optional)</label>
          <input
            value={location}
            onChange={e => setLocation(e.target.value)}
            placeholder="e.g. Bangkok / Remote"
            className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-gray-400 block mb-1.5">Listing URL (optional)</label>
          <input
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder="LinkedIn / careers page link"
            className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
        </div>
      </div>

      <div>
        <label className="text-xs font-medium text-gray-400 block mb-1.5">Job description *</label>
        <textarea
          value={jdText}
          onChange={e => setJdText(e.target.value)}
          placeholder="Paste the full job description here (from LinkedIn, a careers page, or anywhere else)..."
          rows={18}
          className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-600 resize-y font-mono leading-relaxed"
        />
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-600">
          {jdText.trim().length > 0 ? `${jdText.trim().length} characters` : 'Title, company, and job description are required'}
        </p>
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="px-6 py-2.5 bg-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {submitting ? 'Analyzing…' : 'Analyze Job Description'}
        </button>
      </div>
    </div>
  )
}
