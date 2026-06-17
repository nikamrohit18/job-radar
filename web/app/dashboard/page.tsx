import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { SearchForm } from '@/components/search-form'
import { JobFilters } from '@/components/job-filters'
import { JobCard } from '@/components/job-card'
import type { JobOut, JobListParams } from '@/lib/api'

type SearchParams = { [key: string]: string | string[] | undefined }

function parseParams(sp: SearchParams): JobListParams {
  const get = (key: string) => {
    const v = sp[key]
    return Array.isArray(v) ? v[0] : v
  }
  const minScoreRaw = get('min_score')
  const sortBy = get('sort_by')
  const sortDir = get('sort_dir')
  return {
    archived: get('archived') === 'true',
    location: get('location') || undefined,
    company: get('company') || undefined,
    source: get('source') || undefined,
    minScore: minScoreRaw ? Number(minScoreRaw) : undefined,
    sortBy: (sortBy as JobListParams['sortBy']) || undefined,
    sortDir: (sortDir as JobListParams['sortDir']) || undefined,
  }
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>
}) {
  const { userId, getToken } = await auth()
  if (!userId) redirect('/sign-in')

  const token = (await getToken()) ?? ''
  const params = parseParams(await searchParams)

  let jobs: JobOut[] = []
  try {
    jobs = await api.jobs.list(token, { ...params, limit: 50 })
  } catch { /* show empty state */ }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-semibold">Scored Jobs</h1>
      </div>
      <div className="mb-2">
        <SearchForm />
      </div>
      <div className="mb-6 text-right">
        <Link href="/jobs/new" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
          or paste a job description manually →
        </Link>
      </div>

      <JobFilters />

      {jobs.length === 0 ? (
        <div className="text-center py-20 text-gray-500">
          {params.archived ? (
            <p>No archived jobs.</p>
          ) : (
            <>
              <p className="mb-2">No scored jobs match these filters.</p>
              <p className="text-sm">Click &quot;Fetch Jobs&quot; to pull listings and score them against your resume.</p>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map(job => (
            <JobCard key={job.id} job={job} token={token} archived={!!params.archived} />
          ))}
        </div>
      )}
    </div>
  )
}
