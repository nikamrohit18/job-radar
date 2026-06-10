'use client'
import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

export function FetchJobsButton() {
  const { getToken } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  async function handleFetch() {
    setLoading(true)
    setResult(null)
    try {
      const token = (await getToken()) ?? ''
      const res = await api.jobs.fetch(token, {
        source: 'wwr',
        query: 'head of AI',
        location: 'remote',
        days: 7,
      })
      setResult(`${res.new} new · ${res.skipped} skipped`)
      router.refresh()
    } catch (e: unknown) {
      setResult(`Error: ${e instanceof Error ? e.message : 'unknown'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center gap-3">
      {result && <span className="text-xs text-gray-400">{result}</span>}
      <button
        onClick={handleFetch}
        disabled={loading}
        className="px-4 py-2 bg-indigo-600 rounded-lg text-sm hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Fetching…' : 'Fetch Jobs'}
      </button>
    </div>
  )
}
