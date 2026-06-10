import { auth } from '@clerk/nextjs/server'
import { redirect, notFound } from 'next/navigation'
import { api } from '@/lib/api'
import { JobDetailClient } from '@/components/job-detail-client'

export default async function JobPage(props: { params: Promise<{ id: string }> }) {
  const { id } = await props.params
  const { userId, getToken } = await auth()
  if (!userId) redirect('/sign-in')

  const token = (await getToken()) ?? ''
  let job = null
  try {
    job = await api.jobs.get(token, Number(id))
  } catch {
    notFound()
  }

  if (!job) notFound()
  return <JobDetailClient job={job} token={token} />
}
