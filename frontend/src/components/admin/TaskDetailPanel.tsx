import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Loader2, Clock, Zap, AlertTriangle, FileText, Play } from 'lucide-react'
import { SectionLabel, StatusBadge } from '@/components/torale'
import { toast } from 'sonner'
import { stateToVariant } from './types'
import type { TaskData } from './types'

interface Execution {
  id: string
  task_id: string
  status: string
  started_at: string | null
  completed_at: string | null
  result: {
    evidence?: string
    notification?: string
    confidence?: number
  } | null
  error_message: string | null
  notification: string | null
  grounding_sources: unknown[] | null
  search_query: string
  user_email: string
}

interface TaskDetailPanelProps {
  task: TaskData
}

function formatDuration(startedAt: string | null, completedAt: string | null): string {
  if (!startedAt || !completedAt) return '-'
  const ms = new Date(completedAt).getTime() - new Date(startedAt).getTime()
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function TaskDetailPanel({ task }: TaskDetailPanelProps) {
  const [executions, setExecutions] = useState<Execution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [isExecuting, setIsExecuting] = useState(false)

  const handleExecute = async () => {
    setIsExecuting(true)
    try {
      await api.adminExecuteTask(task.id)
      toast.success('Execution started')
      setRetryCount((c) => c + 1) // Refresh executions
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to execute task')
    } finally {
      setIsExecuting(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setLoading(true)
        const data = await api.getAdminExecutions({ task_id: task.id, limit: 20 })
        if (!cancelled) {
          setExecutions(data.executions ?? [])
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load executions')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [task.id, retryCount])

  return (
    <div className="bg-zinc-50 border-t border-zinc-200 p-4 space-y-4">
      {/* Actions */}
      <div className="flex items-center gap-2">
        <SectionLabel>Actions</SectionLabel>
        <button
          onClick={handleExecute}
          disabled={isExecuting}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-zinc-900 text-white text-xs font-mono hover:bg-[hsl(10,90%,55%)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isExecuting ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Play className="h-3 w-3" />
          )}
          Run Now
        </button>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <SectionLabel>State</SectionLabel>
          <div className="mt-1">
            <StatusBadge variant={stateToVariant(task.state)} />
          </div>
        </div>
        <div>
          <SectionLabel>User</SectionLabel>
          <p className="text-xs font-mono text-zinc-700 mt-1">{task.user_email}</p>
        </div>
        <div>
          <SectionLabel>Created</SectionLabel>
          <p className="text-xs font-mono text-zinc-700 mt-1">{formatTimestamp(task.created_at)}</p>
        </div>
        <div>
          <SectionLabel>State Changed</SectionLabel>
          <p className="text-xs font-mono text-zinc-700 mt-1">{formatTimestamp(task.state_changed_at)}</p>
        </div>
        <div>
          <SectionLabel>Next Run</SectionLabel>
          <p className="text-xs font-mono text-zinc-700 mt-1">
            {task.next_run
              ? new Date(task.next_run).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
              : '-'}
          </p>
        </div>
      </div>

      {/* Last Agent Response */}
      <div>
        <SectionLabel>Last Agent Response</SectionLabel>
        <div className="mt-1 p-3 bg-white border border-zinc-200 text-xs font-mono text-zinc-700 whitespace-pre-wrap max-h-40 overflow-y-auto">
          {loading ? (
            'Loading...'
          ) : executions.length > 0 && executions[0].result ? (
            JSON.stringify(executions[0].result, null, 2)
          ) : (
            'No executions yet'
          )}
        </div>
      </div>

      {/* Execution History */}
      <div>
        <SectionLabel>Execution History</SectionLabel>
        {loading ? (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="h-4 w-4 animate-spin text-zinc-400" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xs font-mono text-red-600">{error}</p>
            <button
              onClick={() => setRetryCount(c => c + 1)}
              className="px-2 py-1 text-[10px] font-mono border border-zinc-200 hover:border-zinc-900 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : executions.length === 0 ? (
          <p className="text-xs font-mono text-zinc-400 mt-1">No executions yet</p>
        ) : (
          <div className="mt-1 space-y-2">
            {executions.map((exec) => (
              <ExecutionRow key={exec.id} execution={exec} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function ExecutionRow({ execution }: { execution: Execution }) {
  const confidence = execution.result?.confidence
  const sourceCount = Array.isArray(execution.grounding_sources) ? execution.grounding_sources.length : 0

  return (
    <div className="bg-white border border-zinc-200 p-3 space-y-2">
      <div className="flex items-center gap-3 flex-wrap">
        <StatusBadge variant={stateToVariant(execution.status)} />
        <span className="text-[10px] font-mono text-zinc-500 flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {formatTimestamp(execution.started_at)}
        </span>
        <span className="text-[10px] font-mono text-zinc-400">
          {formatDuration(execution.started_at, execution.completed_at)}
        </span>
        {execution.notification && (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-600">
            <Zap className="h-3 w-3" />
            Notified
          </span>
        )}
        {confidence != null && (
          <span className="text-[10px] font-mono text-zinc-500">
            conf: {typeof confidence === 'number' ? `${confidence}%` : String(confidence)}
          </span>
        )}
        {sourceCount > 0 && (
          <span className="text-[10px] font-mono text-zinc-400 flex items-center gap-1">
            <FileText className="h-3 w-3" />
            {sourceCount} source{sourceCount !== 1 ? 's' : ''}
          </span>
        )}
      </div>

      {execution.result?.notification && (
        <p className="text-xs font-mono text-emerald-700 truncate" title={execution.result.notification}>
          {execution.result.notification}
        </p>
      )}

      {execution.result?.evidence && (
        <details className="text-[10px] font-mono">
          <summary className="cursor-pointer text-zinc-400 hover:text-zinc-600 transition-colors">
            Agent Reasoning
          </summary>
          <pre className="mt-1 p-2 bg-zinc-50 border border-zinc-200 overflow-x-auto text-zinc-600 max-h-40 overflow-y-auto whitespace-pre-wrap">
            {execution.result.evidence}
          </pre>
        </details>
      )}

      {execution.error_message && (
        <p className="text-xs font-mono text-red-600 flex items-center gap-1">
          <AlertTriangle className="h-3 w-3 shrink-0" />
          {execution.error_message}
        </p>
      )}

      {execution.result && (
        <details className="text-[10px] font-mono">
          <summary className="cursor-pointer text-zinc-400 hover:text-zinc-600 transition-colors">
            Raw JSON
          </summary>
          <pre className="mt-1 p-2 bg-zinc-50 border border-zinc-200 overflow-x-auto text-zinc-600 max-h-60 overflow-y-auto">
            {JSON.stringify(execution.result, null, 2)}
          </pre>
        </details>
      )}
    </div>
  )
}
