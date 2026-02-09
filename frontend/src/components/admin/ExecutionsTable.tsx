import { useCallback, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { formatDuration } from '@/lib/utils'
import { ExecutionCard } from './cards/ExecutionCard'
import { Loader2, Activity, ChevronDown, Link2 } from 'lucide-react'
import { SectionLabel, BrutalistCard, StatusBadge } from '@/components/torale'
import { stateToVariant } from './types'
import type { ExecutionData } from './types'

interface ExecutionsTableProps {
  onTaskClick?: (taskId: string) => void
}

export function ExecutionsTable({ onTaskClick }: ExecutionsTableProps = {}) {
  const [executions, setExecutions] = useState<ExecutionData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showDropdown, setShowDropdown] = useState(false)

  const loadExecutions = useCallback(async () => {
    try {
      setLoading(true)
      const params: { limit: number; status?: string } = { limit: 50 }
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      const data = await api.getAdminExecutions(params)
      setExecutions(data.executions)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load executions')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    loadExecutions()
  }, [loadExecutions])

  const statusOptions = [
    { value: 'all', label: 'All statuses' },
    { value: 'success', label: 'Success' },
    { value: 'failed', label: 'Failed' },
    { value: 'running', label: 'Running' },
  ]

  if (loading) {
    return (
      <BrutalistCard className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
      </BrutalistCard>
    )
  }

  if (error) {
    return (
      <BrutalistCard className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-sm font-mono text-red-600">Error: {error}</p>
          <button
            onClick={loadExecutions}
            className="mt-2 px-3 py-1.5 text-xs font-mono border border-zinc-200 hover:border-zinc-900 transition-colors"
          >
            Retry
          </button>
        </div>
      </BrutalistCard>
    )
  }

  return (
    <BrutalistCard>
      {/* Header */}
      <div className="p-4 border-b border-zinc-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-grotesk font-bold">Execution History</h3>
            <p className="text-[10px] font-mono text-zinc-400">
              View all task executions across users
            </p>
          </div>
        </div>

        {/* Custom Select Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center justify-between gap-2 px-3 py-2 w-full sm:w-[180px] border-2 border-zinc-200 bg-white text-sm font-mono text-zinc-900 hover:border-zinc-400 transition-colors"
          >
            {statusOptions.find(o => o.value === statusFilter)?.label}
            <ChevronDown className={`h-4 w-4 text-zinc-400 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
          </button>
          {showDropdown && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowDropdown(false)} />
              <div className="absolute right-0 mt-1 w-full sm:w-[180px] bg-white border-2 border-zinc-900 z-20 shadow-lg">
                {statusOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setStatusFilter(option.value)
                      setShowDropdown(false)
                    }}
                    className={`w-full text-left px-3 py-2 text-sm font-mono hover:bg-zinc-50 transition-colors ${
                      statusFilter === option.value ? 'bg-zinc-900 text-white hover:bg-zinc-900' : ''
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-200 bg-zinc-50">
              <th className="text-left p-3"><SectionLabel>User</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Query</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Status</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Notification</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Started</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Duration</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Sources</SectionLabel></th>
            </tr>
          </thead>
          <tbody>
            {executions.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-8 text-center">
                  <Activity className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
                  <p className="text-xs text-zinc-500 font-mono">No executions found</p>
                </td>
              </tr>
            ) : (
              executions.map((execution) => (
                <tr
                  key={execution.id}
                  className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors"
                >
                  <td className="p-3 text-xs font-mono text-zinc-600">{execution.user_email}</td>
                  <td className="p-3">
                    <button
                      onClick={() => onTaskClick?.(execution.task_id)}
                      className="text-left w-full text-xs font-mono text-zinc-700 hover:text-zinc-900 hover:underline max-w-xs truncate"
                    >
                      {execution.search_query}
                    </button>
                  </td>
                  <td className="p-3">
                    <StatusBadge variant={stateToVariant(execution.status)} />
                  </td>
                  <td className="p-3 text-xs font-mono text-zinc-600 max-w-xs truncate">
                    {execution.notification || '—'}
                  </td>
                  <td className="p-3 text-xs font-mono text-zinc-500">
                    {execution.started_at
                      ? formatDistanceToNow(new Date(execution.started_at), { addSuffix: true })
                      : '-'}
                  </td>
                  <td className="p-3 text-xs font-mono text-zinc-900">
                    {formatDuration(execution.started_at, execution.completed_at, '-')}
                  </td>
                  <td className="p-3">
                    <span className="inline-flex items-center gap-1 text-xs font-mono text-zinc-600">
                      <Link2 className="h-3 w-3" />
                      {execution.grounding_sources?.length || 0}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="block md:hidden p-4 space-y-3">
        {executions.length === 0 ? (
          <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
            <Activity className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
            <p className="text-xs text-zinc-500 font-mono">No executions found</p>
          </div>
        ) : (
          executions.map((execution) => <ExecutionCard key={execution.id} execution={execution} />)
        )}
      </div>
    </BrutalistCard>
  )
}
