'use client'
import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'

export function ResumeForm({ token: initialToken, hasResume }: { token: string; hasResume: boolean }) {
  const { getToken } = useAuth()
  const router = useRouter()
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSave() {
    if (!content.trim()) return
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      const token = (await getToken()) ?? initialToken
      await api.users.updateResume(token, content.trim())
      setSaved(true)
      router.refresh()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to save resume')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      {hasResume && !saved && (
        <div className="text-sm text-green-400 bg-green-400/10 border border-green-400/20 rounded-lg px-4 py-2.5">
          Resume already saved — paste a new version below to replace it.
        </div>
      )}
      {saved && (
        <div className="text-sm text-green-400 bg-green-400/10 border border-green-400/20 rounded-lg px-4 py-2.5">
          Resume saved successfully.
        </div>
      )}
      <textarea
        value={content}
        onChange={e => setContent(e.target.value)}
        placeholder="Paste your full resume text here (plain text or copied from Word/PDF)..."
        rows={22}
        className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-600 resize-y font-mono leading-relaxed"
      />
      {error && <p className="text-red-400 text-sm">{error}</p>}
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-600">
          {content.trim().length > 0 ? `${content.trim().length} characters` : 'Plain text works best'}
        </p>
        <button
          onClick={handleSave}
          disabled={saving || !content.trim()}
          className="px-6 py-2.5 bg-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {saving ? 'Saving…' : 'Save Resume'}
        </button>
      </div>
    </div>
  )
}
