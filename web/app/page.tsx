import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import Link from 'next/link'

export default async function Home() {
  const { userId } = await auth()
  if (userId) redirect('/dashboard')

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <h1 className="text-4xl font-bold mb-3">job-radar</h1>
      <p className="text-gray-400 mb-8 max-w-md text-sm leading-relaxed">
        AI-powered job scoring and application tracking for senior roles.
        Score jobs against your resume, generate cover letters, and track your pipeline.
      </p>
      <Link
        href="/sign-in"
        className="px-6 py-3 bg-indigo-600 rounded-lg hover:bg-indigo-500 transition-colors text-sm font-medium"
      >
        Sign in
      </Link>
    </div>
  )
}
