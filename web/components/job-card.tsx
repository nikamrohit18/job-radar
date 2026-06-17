'use client'
import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { useToast } from '@/components/toast'
import type { JobOut } from '@/lib/api'

function scoreColor(score: number) {
  if (score >= 70) return 'text-green-400'
  if (score >= 50) return 'text-yellow-400'
  return 'text-red-400'
}

function formatDateTime(iso: string | null | undefined) {
  if (!iso) return null
  return new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
}

export function JobCard({ job, token, archived }: { job: JobOut; token: string; archived: boolean }) {
  const { getToken } = useAuth()
  const router = useRouter()
  const toast = useToast()
  const [busy, setBusy] = useState(false)

  async function handleArchiveToggle(e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()
    setBusy(true)
    try {
      const t = (await getToken()) ?? token
      if (archived) {
        await api.jobs.restore(t, job.id)
        toast.success('Job restored to your active dashboard.')
      } else {
        await api.jobs.archive(t, job.id)
        toast.success('Job archived. Your scoring history for it is kept.')
      }
      router.refresh()
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setBusy(false)
    }
  }

  const s = job.score
  const posted = formatDateTime(job.date_posted)
  const scored = formatDateTime(s?.scored_at)

  return (
    <Link href={`/jobs/${job.id}`}>
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors cursor-pointer">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="font-medium text-white truncate">{job.title}</p>
            <p className="text-sm text-gray-400 mt-0.5">
              {job.company} · {job.location ?? 'Remote'}
            </p>
            {(posted || scored) && (
              <p className="text-xs text-gray-600 mt-1">
                {posted && <>Posted {posted}</>}
                {posted && scored && ' · '}
                {scored && <>Scored {scored}</>}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {s && (
              <div className="flex gap-4 text-right">
                <div>
                  <p className={`text-xl font-bold ${scoreColor(s.ats_score)}`}>{s.ats_score}</p>
                  <p className="text-xs text-gray-500">ATS</p>
                </div>
                <div>
                  <p className="text-xl font-bold text-indigo-400">{s.interview_probability}%</p>
                  <p className="text-xs text-gray-500">Interview</p>
                </div>
              </div>
            )}
            <button
              onClick={handleArchiveToggle}
              disabled={busy}
              className="text-xs text-gray-500 hover:text-white disabled:opacity-40 transition-colors px-2 py-1 rounded-md hover:bg-gray-800"
            >
              {archived ? 'Restore' : 'Archive'}
            </button>
          </div>
        </div>
        {s && (
          <p className="text-xs text-gray-500 mt-2 line-clamp-2">{s.summary}</p>
        )}
      </div>
    </Link>
  )
}
