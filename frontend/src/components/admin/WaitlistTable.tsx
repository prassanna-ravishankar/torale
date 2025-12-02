import { useCallback, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { toast } from 'sonner'
import { WaitlistEntryCard } from './cards/WaitlistEntryCard'
import { Loader2, Users, Copy, Trash2, CheckCircle2, Clock, UserCheck } from 'lucide-react'

interface WaitlistEntry {
  id: string
  email: string
  created_at: string
  status: string
  invited_at: string | null
  notes: string | null
}

interface WaitlistStats {
  pending: number
  invited: number
  converted: number
  total: number
}

export function WaitlistTable() {
  const [entries, setEntries] = useState<WaitlistEntry[]>([])
  const [stats, setStats] = useState<WaitlistStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  const loadWaitlist = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getWaitlist(statusFilter || undefined)
      setEntries(data)
    } catch (error) {
      console.error('Failed to load waitlist:', error)
      toast.error('Failed to load waitlist')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  const loadStats = useCallback(async () => {
    try {
      const data = await api.getWaitlistStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }, [])

  useEffect(() => {
    loadWaitlist()
    loadStats()
  }, [loadWaitlist, loadStats])

  const deleteEntry = async (entryId: string) => {
    if (!confirm('Are you sure you want to remove this entry?')) return

    try {
      await api.deleteWaitlistEntry(entryId)
      toast.success('Entry removed')
      loadWaitlist()
      loadStats()
    } catch (error) {
      console.error('Failed to delete entry:', error)
      toast.error('Failed to remove entry')
    }
  }

  const copyEmail = (email: string) => {
    navigator.clipboard.writeText(email)
    toast.success('Email copied to clipboard')
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'converted':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-mono uppercase tracking-wider border border-emerald-200">
            <CheckCircle2 className="h-3 w-3" />
            Converted
          </span>
        )
      case 'invited':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-50 text-blue-700 text-[10px] font-mono uppercase tracking-wider border border-blue-200">
            <UserCheck className="h-3 w-3" />
            Invited
          </span>
        )
      case 'pending':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-amber-50 text-amber-700 text-[10px] font-mono uppercase tracking-wider border border-amber-200">
            <Clock className="h-3 w-3" />
            Pending
          </span>
        )
    }
  }

  if (loading && !entries.length) {
    return (
      <div className="flex items-center justify-center h-64 bg-white border-2 border-zinc-200">
        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
      </div>
    )
  }

  const filterButtons = [
    { value: null, label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'converted', label: 'Converted' },
  ]

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-3">
          {/* Total */}
          <div className="bg-white border-2 border-zinc-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                Total
              </span>
              <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center">
                <Users className="h-4 w-4 text-zinc-600" />
              </div>
            </div>
            <p className="text-2xl font-grotesk font-bold tracking-tight">{stats.total}</p>
          </div>

          {/* Pending */}
          <div className="bg-white border-2 border-zinc-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                Pending
              </span>
              <div className="bg-amber-50 w-8 h-8 flex items-center justify-center border border-amber-200">
                <Clock className="h-4 w-4 text-amber-600" />
              </div>
            </div>
            <p className="text-2xl font-grotesk font-bold tracking-tight text-amber-600">{stats.pending}</p>
          </div>

          {/* Converted */}
          <div className="bg-white border-2 border-zinc-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                Converted
              </span>
              <div className="bg-emerald-50 w-8 h-8 flex items-center justify-center border border-emerald-200">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              </div>
            </div>
            <p className="text-2xl font-grotesk font-bold tracking-tight text-emerald-600">{stats.converted}</p>
          </div>
        </div>
      )}

      {/* Waitlist Table */}
      <div className="bg-white border-2 border-zinc-200">
        {/* Header */}
        <div className="p-4 border-b border-zinc-200 flex items-center gap-3">
          <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
            <Users className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-grotesk font-bold">Waitlist Entries</h3>
            <p className="text-[10px] font-mono text-zinc-400">
              Manage users waiting for access
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 border-b border-zinc-200 flex flex-wrap gap-2">
          {filterButtons.map((btn) => (
            <button
              key={btn.value ?? 'all'}
              onClick={() => setStatusFilter(btn.value)}
              className={`px-3 py-1.5 text-xs font-mono transition-colors ${
                statusFilter === btn.value
                  ? 'bg-zinc-900 text-white'
                  : 'border border-zinc-200 text-zinc-600 hover:border-zinc-400'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>

        {entries.length === 0 ? (
          <div className="p-8 text-center">
            <Users className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
            <p className="text-xs text-zinc-500 font-mono">No waitlist entries found</p>
          </div>
        ) : (
          <>
            {/* Desktop Table View */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-zinc-200 bg-zinc-50">
                    <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Email</th>
                    <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Joined</th>
                    <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Status</th>
                    <th className="text-right p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr key={entry.id} className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors">
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-mono text-zinc-900">{entry.email}</span>
                          <button
                            onClick={() => copyEmail(entry.email)}
                            className="p-1 text-zinc-400 hover:text-zinc-900 transition-colors"
                          >
                            <Copy className="h-3 w-3" />
                          </button>
                        </div>
                      </td>
                      <td className="p-3 text-xs font-mono text-zinc-500">
                        {new Date(entry.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-3">{getStatusBadge(entry.status)}</td>
                      <td className="p-3 text-right">
                        <button
                          onClick={() => deleteEntry(entry.id)}
                          className="p-1.5 text-zinc-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Card View */}
            <div className="block md:hidden p-4 space-y-3">
              {entries.map((entry) => (
                <WaitlistEntryCard
                  key={entry.id}
                  entry={entry}
                  onCopyEmail={copyEmail}
                  onDelete={deleteEntry}
                  getStatusBadge={getStatusBadge}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
