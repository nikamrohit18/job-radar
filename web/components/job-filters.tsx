'use client'
import { useState } from 'react'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'

const SORT_OPTIONS = [
  { value: 'ats_score:desc', label: 'ATS Score (high → low)' },
  { value: 'ats_score:asc', label: 'ATS Score (low → high)' },
  { value: 'interview_probability:desc', label: 'Interview % (high → low)' },
  { value: 'interview_probability:asc', label: 'Interview % (low → high)' },
  { value: 'date_posted:desc', label: 'Date Posted (newest)' },
  { value: 'date_posted:asc', label: 'Date Posted (oldest)' },
  { value: 'scored_at:desc', label: 'Date Scored (newest)' },
  { value: 'scored_at:asc', label: 'Date Scored (oldest)' },
]

const SOURCES = [
  { value: '', label: 'All sources' },
  { value: 'wwr', label: 'We Work Remotely' },
  { value: 'remotive', label: 'Remotive' },
  { value: 'indeed', label: 'Indeed' },
  { value: 'manual', label: 'Pasted JD' },
]

export function JobFilters() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const archived = searchParams.get('archived') === 'true'
  const sortBy = searchParams.get('sort_by') ?? 'ats_score'
  const sortDir = searchParams.get('sort_dir') ?? 'desc'
  const source = searchParams.get('source') ?? ''

  const [location, setLocation] = useState(searchParams.get('location') ?? '')
  const [company, setCompany] = useState(searchParams.get('company') ?? '')
  const [minScore, setMinScore] = useState(searchParams.get('min_score') ?? '')

  function update(updates: Record<string, string | null>) {
    const params = new URLSearchParams(searchParams.toString())
    for (const [key, value] of Object.entries(updates)) {
      if (value) params.set(key, value)
      else params.delete(key)
    }
    router.push(`${pathname}?${params.toString()}`)
  }

  const hasFilters = location || company || source || minScore

  function clearFilters() {
    setLocation('')
    setCompany('')
    setMinScore('')
    update({ location: null, company: null, source: null, min_score: null })
  }

  return (
    <div className="space-y-3 mb-4">
      <div className="flex gap-2 border-b border-gray-800">
        <button
          onClick={() => update({ archived: null })}
          className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
            !archived ? 'border-indigo-500 text-white' : 'border-transparent text-gray-400 hover:text-white'
          }`}
        >
          Active
        </button>
        <button
          onClick={() => update({ archived: 'true' })}
          className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
            archived ? 'border-indigo-500 text-white' : 'border-transparent text-gray-400 hover:text-white'
          }`}
        >
          Archived
        </button>
      </div>

      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs text-gray-500 block mb-1">Location</label>
          <input
            value={location}
            onChange={e => setLocation(e.target.value)}
            onBlur={() => update({ location: location.trim() || null })}
            onKeyDown={e => e.key === 'Enter' && update({ location: location.trim() || null })}
            placeholder="e.g. remote"
            className="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500 w-32"
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Company</label>
          <input
            value={company}
            onChange={e => setCompany(e.target.value)}
            onBlur={() => update({ company: company.trim() || null })}
            onKeyDown={e => e.key === 'Enter' && update({ company: company.trim() || null })}
            placeholder="e.g. Acme"
            className="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500 w-32"
          />
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Source</label>
          <select
            value={source}
            onChange={e => update({ source: e.target.value || null })}
            className="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-gray-500"
          >
            {SOURCES.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-gray-500 block mb-1">Min ATS score</label>
          <input
            type="number"
            min={0}
            max={100}
            value={minScore}
            onChange={e => setMinScore(e.target.value)}
            onBlur={() => update({ min_score: minScore.trim() || null })}
            onKeyDown={e => e.key === 'Enter' && update({ min_score: minScore.trim() || null })}
            placeholder="0"
            className="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500 w-20"
          />
        </div>
        <div className="ml-auto">
          <label className="text-xs text-gray-500 block mb-1">Sort by</label>
          <select
            value={`${sortBy}:${sortDir}`}
            onChange={e => {
              const [by, dir] = e.target.value.split(':')
              update({ sort_by: by, sort_dir: dir })
            }}
            className="bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-gray-500"
          >
            {SORT_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        {hasFilters && (
          <button
            onClick={clearFilters}
            className="text-xs text-gray-500 hover:text-red-400 transition-colors px-2 py-1.5"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  )
}
