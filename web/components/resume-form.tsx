'use client'
import { useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { useToast } from '@/components/toast'
import type { ResumeVersionOut } from '@/lib/api'

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })
}

function VersionCard({
  version,
  token,
}: {
  version: ResumeVersionOut
  token: string
}) {
  const { getToken } = useAuth()
  const router = useRouter()
  const toast = useToast()
  const [expanded, setExpanded] = useState(false)
  const [activating, setActivating] = useState(false)

  async function handleActivate() {
    setActivating(true)
    try {
      const t = (await getToken()) ?? token
      await api.users.activateResume(t, version.id)
      toast.success('Switched your active resume.')
      router.refresh()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Failed to switch resume')
    } finally {
      setActivating(false)
    }
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-white truncate">
            {version.label || 'Saved resume'}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">{formatDateTime(version.created_at)}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {version.is_active ? (
            <span className="text-xs text-green-400 bg-green-400/10 border border-green-400/20 rounded-full px-2.5 py-1">
              Active
            </span>
          ) : (
            <button
              onClick={handleActivate}
              disabled={activating}
              className="text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-50 transition-colors px-2 py-1"
            >
              {activating ? 'Switching…' : 'Set Active'}
            </button>
          )}
          <button
            onClick={() => setExpanded(v => !v)}
            className="text-xs text-gray-500 hover:text-white transition-colors px-2 py-1 rounded-md hover:bg-gray-800"
          >
            {expanded ? 'Hide' : 'View'}
          </button>
        </div>
      </div>
      {expanded && (
        <pre className="mt-3 max-h-96 overflow-y-auto bg-gray-950 border border-gray-800 rounded-lg px-4 py-3 text-sm text-gray-300 whitespace-pre-wrap leading-relaxed font-mono">
          {version.content}
        </pre>
      )}
    </div>
  )
}

export function ResumeForm({ token: initialToken, resumes }: { token: string; resumes: ResumeVersionOut[] }) {
  const { getToken } = useAuth()
  const router = useRouter()
  const toast = useToast()
  const [creating, setCreating] = useState(resumes.length === 0)
  const [content, setContent] = useState('')
  const [label, setLabel] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSave() {
    if (!content.trim()) return
    setSaving(true)
    try {
      const token = (await getToken()) ?? initialToken
      await api.users.saveResume(token, { content: content.trim(), label: label.trim() || undefined })
      toast.success('Resume saved and set as active.')
      setCreating(false)
      setContent('')
      setLabel('')
      router.refresh()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : 'Failed to save resume')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      {resumes.length > 0 && !creating && (
        <div className="flex justify-end">
          <button
            onClick={() => setCreating(true)}
            className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            + Save new resume version
          </button>
        </div>
      )}

      {creating && (
        <div className="space-y-3 bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div>
            <label className="text-xs font-medium text-gray-400 block mb-1.5">Label (optional)</label>
            <input
              value={label}
              onChange={e => setLabel(e.target.value)}
              placeholder="e.g. Updated from LinkedIn"
              className="w-full bg-gray-800 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-500"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-400 block mb-1.5">Resume text</label>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              placeholder="Paste your full resume text here (plain text or copied from Word/PDF)..."
              rows={20}
              className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-3 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-gray-600 resize-y font-mono leading-relaxed"
            />
          </div>
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-600">
              {content.trim().length > 0 ? `${content.trim().length} characters` : 'Plain text works best'}
            </p>
            <div className="flex gap-2">
              {resumes.length > 0 && (
                <button
                  onClick={() => { setCreating(false); setContent(''); setLabel('') }}
                  className="px-4 py-2.5 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
              )}
              <button
                onClick={handleSave}
                disabled={saving || !content.trim()}
                className="px-6 py-2.5 bg-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {saving ? 'Saving…' : 'Save & Activate'}
              </button>
            </div>
          </div>
        </div>
      )}

      {resumes.length > 0 && (
        <div className="space-y-3">
          {resumes.map(v => (
            <VersionCard key={v.id} version={v} token={initialToken} />
          ))}
        </div>
      )}
    </div>
  )
}
