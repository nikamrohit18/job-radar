import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { JdPasteForm } from '@/components/jd-paste-form'

export default async function NewJobPage() {
  const { userId, getToken } = await auth()
  if (!userId) redirect('/sign-in')

  const token = (await getToken()) ?? ''

  return (
    <div>
      <h1 className="text-xl font-semibold mb-2">Paste a Job Description</h1>
      <p className="text-gray-400 text-sm mb-8">
        Paste a job description from LinkedIn, a company careers page, or any job site.
        Claude scores it against your resume, flags gaps and missing ATS keywords, and can
        rewrite your resume for this specific role.
      </p>
      <JdPasteForm token={token} />
    </div>
  )
}
