'use client'
import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'

const DEFAULT_QUERIES = [
  'AI product manager',
  'engineering manager',
  'VP of engineering',
  'head of engineering',
  'head of AI',
  'VP of digital transformation',
]

type Totals = { new: number; skipped: number; errors: number; lastError: string | null }

export function SearchForm() {
  const { getToken } = useAuth()
  const router = useRouter()

  const [expanded, setExpanded] = useState(false)
  const [queries, setQueries] = useState<string[]>(DEFAULT_QUERIES)
  const [source, setSource] = useState<'remotive' | 'wwr'>('remotive')
  const [days, setDays] = useState(14)
  const [limit, setLimit] = useState(20)
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState<string | null>(null)
  const [totals, setTotals] = useState<Totals | null>(null)
  const [noResume, setNoResume] = useState(false)

  function updateQuery(i: number, val: string) {
    setQueries(prev => prev.map((q, idx) => (idx === i ? val : q)))
  }

  function removeQuery(i: number) {
    setQueries(prev => prev.filter((_, idx) => idx !== i))
  }

  async function handleFetch() {
    const active = queries.filter(q => q.trim())
    if (!active.length) return

    setRunning(true)
    setTotals(null)
    setNoResume(false)
    const token = (await getToken()) ?? ''
    const acc: Totals = { new: 0, skipped: 0, errors: 0, lastError: null }

    for (let i = 0; i < active.length; i++) {
      setProgress(`${i + 1}/${active.length}: "${active[i]}"`)
      try {
        const res = await api.jobs.fetch(token, {
          source,
          query: active[i],
          location: 'remote',
          days,
          limit,
        })
        acc.new += res.new
        acc.skipped += res.skipped
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : ''
        if (msg.toLowerCase().includes('no resume')) {
          setNoResume(true)
          break
        }
        acc.errors++
        acc.lastError = msg || 'unknown error'
      }
    }

    setProgress(null)
    setTotals(acc)
    setRunning(false)
    router.refresh()
  }

  return (
    <div>
      <div className="flex items-center justify-end gap-3">
        {noResume && (
          <span className="text-xs text-amber-400">
            No resume —{' '}
            <Link href="/profile" className="underline hover:text-amber-300">
              upload one first
            </Link>
          </span>
        )}
        {totals && !noResume && (
          <span className="text-xs text-gray-400">
            {totals.new} new · {totals.skipped} skipped
            {totals.errors > 0 && (
              <span className="text-red-400" title={totals.lastError ?? ''}>
                {` · ${totals.errors} failed`}
              </span>
            )}
          </span>
        )}
        {progress && (
          <span className="text-xs text-gray-400">Fetching {progress}…</span>
        )}
        <button
          onClick={() => setExpanded(v => !v)}
          disabled={running}
          className="text-xs text-gray-500 hover:text-gray-300 disabled:opacity-40 transition-colors"
        >
          {expanded ? 'Hide ↑' : 'Settings ↓'}
        </button>
        <button
          onClick={handleFetch}
          disabled={running}
          className="px-4 py-2 bg-indigo-600 rounded-lg text-sm hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {running ? 'Fetching…' : 'Fetch Jobs'}
        </button>
      </div>

      {expanded && (
        <div className="mt-3 bg-gray-900 border border-gray-800 rounded-lg p-4 space-y-4">
          <div>
            <label className="text-xs font-medium text-gray-400 block mb-2">
              Job titles — each runs as a separate search
            </label>
            <div className="space-y-2">
              {queries.map((q, i) => (
                <div key={i} className="flex gap-2">
                  <input
                    value={q}
                    onChange={e => updateQuery(i, e.target.value)}
                    placeholder="e.g. head of AI"
                    className="flex-1 bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500"
                  />
                  <button
                    onClick={() => removeQuery(i)}
                    className="px-2 text-gray-600 hover:text-red-400 transition-colors"
                  >
                    ×
                  </button>
                </div>
              ))}
              <button
                onClick={() => setQueries(prev => [...prev, ''])}
                className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                + Add title
              </button>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-xs font-medium text-gray-400 block mb-1.5">Source</label>
              <select
                value={source}
                onChange={e => setSource(e.target.value as 'remotive' | 'wwr')}
                className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-gray-500"
              >
                <option value="remotive">Remotive (remote only)</option>
                <option value="wwr">We Work Remotely</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-400 block mb-1.5">Days back</label>
              <input
                type="number"
                value={days}
                min={1}
                max={30}
                onChange={e => setDays(Number(e.target.value))}
                className="w-24 bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-gray-500"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-400 block mb-1.5">Limit / query</label>
              <input
                type="number"
                value={limit}
                min={5}
                max={50}
                onChange={e => setLimit(Number(e.target.value))}
                className="w-24 bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:border-gray-500"
              />
            </div>
          </div>

          <p className="text-xs text-gray-600">
            Bangkok · Dubai · Singapore · Malaysia on-site roles — location-specific search coming soon.
          </p>
        </div>
      )}
    </div>
  )
}
