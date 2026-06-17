'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { UserButton, useAuth } from '@clerk/nextjs'

export function Nav() {
  const path = usePathname()
  const { isSignedIn } = useAuth()

  const navLink = (href: string, label: string) => (
    <Link
      href={href}
      className={`text-sm px-3 py-1.5 rounded-md transition-colors ${
        path.startsWith(href)
          ? 'bg-gray-800 text-white'
          : 'text-gray-400 hover:text-white'
      }`}
    >
      {label}
    </Link>
  )

  return (
    <nav className="border-b border-gray-800 px-4">
      <div className="max-w-5xl mx-auto h-14 flex items-center gap-4">
        <Link href="/" className="font-semibold text-white text-sm mr-2">
          job-radar
        </Link>
        {isSignedIn && (
          <>
            {navLink('/dashboard', 'Jobs')}
            {navLink('/jobs/new', 'Paste JD')}
            {navLink('/pipeline', 'Pipeline')}
            {navLink('/profile', 'Profile')}
          </>
        )}
        <div className="ml-auto">
          {isSignedIn ? (
            <UserButton />
          ) : (
            <Link href="/sign-in" className="text-sm text-gray-400 hover:text-white">
              Sign in
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}
