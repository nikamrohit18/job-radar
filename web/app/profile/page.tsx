import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import { api } from '@/lib/api'
import { ResumeForm } from '@/components/resume-form'

export default async function ProfilePage() {
  const { userId, getToken } = await auth()
  if (!userId) redirect('/sign-in')

  const token = (await getToken()) ?? ''
  const user = await api.users.me(token)

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold mb-2">Profile</h1>
      <p className="text-gray-400 text-sm mb-8">
        Paste your resume below. Claude uses it to score jobs, generate cover letters, and tailor interview prep.
      </p>
      <ResumeForm token={token} hasResume={user.has_resume} />
    </div>
  )
}
