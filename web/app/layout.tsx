import type { Metadata } from 'next'
import { Geist } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'
import { Nav } from '@/components/nav'

const geist = Geist({ subsets: ['latin'], variable: '--font-geist' })

export const metadata: Metadata = {
  title: 'job-radar',
  description: 'AI-powered job scoring and application tracking',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" className={geist.variable}>
        <body className="min-h-screen bg-gray-950 text-gray-100 font-sans">
          <Nav />
          <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
        </body>
      </html>
    </ClerkProvider>
  )
}
