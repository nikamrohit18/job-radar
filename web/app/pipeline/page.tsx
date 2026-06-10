import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { api } from '@/lib/api'
import type { ApplicationOut } from '@/lib/api'

const STATUS_LABELS: Record<string, string> = {
  applied: 'Applied',
  screening: 'Screening',
  interview: 'Interview',
  offer: 'Offer',
  rejected: 'Rejected',
  withdrawn: 'Withdrawn',
}
const STATUS_ORDER = ['applied', 'screening', 'interview', 'offer', 'rejected', 'withdrawn']

function daysAgo(dateStr: string) {
  const days = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000)
  if (days === 0) return 'today'
  if (days === 1) return '1 day ago'
  return `${days} days ago`
}

function AppRow({ app }: { app: ApplicationOut }) {
  const job = app.job
  if (!job) return null
  const staleDays = Math.floor((Date.now() - new Date(app.updated_at).getTime()) / 86400000)
  const needsFollowUp = app.status === 'applied' && staleDays >= 7

  return (
    <div className="flex items-center justify-between py-2.5 px-4 hover:bg-gray-800/50 transition-colors">
      <div className="min-w-0">
        <p className="text-sm font-medium text-white truncate">{job.title}</p>
        <p className="text-xs text-gray-500">{job.company}</p>
      </div>
      <div className="flex items-center gap-3 shrink-0 ml-4 text-xs">
        {app.score && <span className="text-gray-500">{app.score.ats_score}/100</span>}
        <span className="text-gray-500">{daysAgo(app.updated_at)}</span>
        {needsFollowUp && <span className="text-yellow-500">follow up</span>}
      </div>
    </div>
  )
}

export default async function PipelinePage() {
  const { userId, getToken } = await auth()
  if (!userId) redirect('/sign-in')

  const token = (await getToken()) ?? ''
  let pipeline = null
  try {
    pipeline = await api.applications.pipeline(token)
  } catch { /* show empty state */ }

  const total = pipeline ? Object.values(pipeline).flat().length : 0

  return (
    <div>
      <h1 className="text-xl font-semibold mb-6">Application Pipeline</h1>

      {total === 0 ? (
        <div className="text-center py-20 text-gray-500">
          <p className="mb-2">No applications tracked yet.</p>
          <p className="text-sm">Open a job and click "Mark as Applied" to start tracking.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {STATUS_ORDER.map(status => {
            const apps: ApplicationOut[] = pipeline?.[status as keyof typeof pipeline] ?? []
            return (
              <div key={status}>
                <div className="flex items-center gap-2 mb-2">
                  <h2 className="text-sm font-medium text-gray-300">{STATUS_LABELS[status]}</h2>
                  <span className="text-xs text-gray-600">{apps.length}</span>
                </div>
                <div className="bg-gray-900 border border-gray-800 rounded-lg divide-y divide-gray-800 overflow-hidden">
                  {apps.length === 0 ? (
                    <p className="text-xs text-gray-600 px-4 py-2">—</p>
                  ) : (
                    apps.map(app => <AppRow key={app.id} app={app} />)
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
