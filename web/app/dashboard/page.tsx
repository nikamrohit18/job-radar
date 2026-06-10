import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { SearchForm } from '@/components/search-form'
import type { JobOut } from '@/lib/api'

function scoreColor(score: number) {
  if (score >= 70) return 'text-green-400'
  if (score >= 50) return 'text-yellow-400'
  return 'text-red-400'
}

function JobCard({ job }: { job: JobOut }) {
  const s = job.score
  return (
    <Link href={`/jobs/${job.id}`}>
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 transition-colors cursor-pointer">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="font-medium text-white truncate">{job.title}</p>
            <p className="text-sm text-gray-400 mt-0.5">
              {job.company} · {job.location ?? 'Remote'}
            </p>
          </div>
          {s && (
            <div className="flex gap-4 text-right shrink-0">
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
        </div>
        {s && (
          <p className="text-xs text-gray-500 mt-2 line-clamp-2">{s.summary}</p>
        )}
      </div>
    </Link>
  )
}

export default async function DashboardPage() {
  const { userId, getToken } = await auth()
  if (!userId) redirect('/sign-in')

  const token = (await getToken()) ?? ''
  let jobs: JobOut[] = []
  try {
    jobs = await api.jobs.list(token, 30)
  } catch { /* show empty state */ }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-semibold">Scored Jobs</h1>
      </div>
      <div className="mb-6">
        <SearchForm />
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p className="mb-2">No scored jobs yet.</p>
          <p className="text-sm">Click "Fetch Jobs" to pull listings and score them against your resume.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map(job => <JobCard key={job.id} job={job} />)}
        </div>
      )}
    </div>
  )
}
