'use client'
import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { useToast } from '@/components/toast'

export function ResumeForm({ token: initialToken, resume }: { token: string; resume: string | null }) {
  const { getToken } = useAuth()
  const router = useRouter()
  const toast = useToast()
  const [editing, setEditing] = useState(!resume)
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSave() {
    if (!content.trim()) return
    setSaving(true)
    try {
      const token = (await getToken()) ?? initialToken
      await api.users.updateResume(token, content.trim())
      toast.success('Resume saved.')
      setEditing(false)
      setContent('')
      router.refresh()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Failed to save resume')
    } finally {
      setSaving(false)
    }
  }

  if (!editing && resume) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-gray-300">Current resume on file</h2>
          <button
            onClick={() => setEditing(true)}
            className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            Replace resume
          </button>
        </div>
        <pre className="w-full max-h-[32rem] overflow-y-auto bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 text-sm text-gray-300 whitespace-pre-wrap leading-relaxed font-mono">
          {resume}
        </pre>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-xs font-medium text-gray-400">
          {resume ? 'Paste the replacement resume text below' : 'Paste your full resume text below'}
        </label>
        {resume && (
          <button
            onClick={() => { setEditing(false); setContent('') }}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Cancel
          </button>
        )}
      </div>
      <textarea
        value={content}
        onChange={e => setContent(e.target.value)}
        placeholder="Paste your full resume text here (plain text or copied from Word/PDF)..."
        rows={22}
        className="w-full bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-600 resize-y font-mono leading-relaxed"
      />
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
