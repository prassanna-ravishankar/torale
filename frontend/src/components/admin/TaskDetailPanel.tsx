import { useEffect, useState } from 'react'
import { formatShortDateTime, getErrorMessage } from '@/lib/utils'
import { useApi } from '@/hooks/useApi';
import { Loader2, Clock, Zap, AlertTriangle, FileText, Play, Pause, RotateCcw } from 'lucide-react'
import { SectionLabel, StatusBadge } from '@/components/torale'
import { toast } from 'sonner'
import { stateToVariant } from './types'
import type { TaskData, ExecutionData } from './types'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

interface TaskDetailPanelProps {
  task: TaskData
  onTaskUpdate?: () => void
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

function formatShortTimestamp(iso: string | null): string {
  if (!iso) return '-'
  return formatShortDateTime(iso)
}

export function TaskDetailPanel({ task, onTaskUpdate }: TaskDetailPanelProps) {
  const api = useApi()
  const [executions, setExecutions] = useState<ExecutionData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [isExecuting, setIsExecuting] = useState(false)
  const [isPauseResuming, setIsPauseResuming] = useState(false)
  const [isResetting, setIsResetting] = useState(false)
  const [isResetDialogOpen, setIsResetDialogOpen] = useState(false)
  const isBusy = isExecuting || isPauseResuming || isResetting

  const handleExecute = async () => {
    setIsExecuting(true)
    try {
      await api.adminExecuteTask(task.id)
      toast.success('Execution started')
      setRetryCount((c) => c + 1)
    } catch (err) {
      const errorMsg = getErrorMessage(err, 'Unknown error')
      console.error(`[TaskDetailPanel] Execute failed for task ${task.id}:`, err)
      toast.error(
        `Failed to start execution: ${errorMsg}. Check task status and try again.`,
        { duration: 6000 }
      )
    } finally {
      setIsExecuting(false)
    }
  }

  const handlePauseResume = async () => {
    setIsPauseResuming(true)
    try {
      const newState = task.state === 'active' ? 'paused' : 'active'
      await api.adminUpdateTaskState(task.id, newState)
      toast.success(newState === 'active' ? 'Watch resumed' : 'Watch paused')

      // Refresh parent and local state
      try {
        onTaskUpdate?.()
      } catch (callbackErr) {
        console.error('Failed to refresh task list:', callbackErr)
      }
      setRetryCount((c) => c + 1)
    } catch (err) {
      const errorMessage = getErrorMessage(err, "Couldn't update the watch")

      // Provide specific guidance based on error type
      if (errorMessage.includes('Invalid state transition')) {
        toast.error('Cannot change watch state from current status. Refresh and try again.')
      } else if (errorMessage.includes('not found')) {
        toast.error('Watch no longer exists. Refreshing...')
        onTaskUpdate?.()
      } else if (errorMessage.includes('inconsistent state')) {
        toast.error('Watch state update failed. Contact support if issue persists.')
      } else {
        toast.error(`Couldn't update the watch: ${errorMessage}`)
      }
    } finally {
      setIsPauseResuming(false)
    }
  }

  const handleResetAndRun = async () => {
    const days = 1
    setIsResetDialogOpen(false)
    setIsResetting(true)
    let resetSucceeded = false

    try {
      // Step 1: Reset (delete history)
      const resetResult = await api.adminResetTask(task.id, days)
      resetSucceeded = true
      toast.success(`Deleted ${resetResult.executions_deleted} execution(s)`)

      // Step 2: Execute task (false = enable notifications)
      await api.adminExecuteTask(task.id, false)
      toast.success('Watch re-executed successfully')

      onTaskUpdate?.()
      setRetryCount((c) => c + 1)
    } catch (err) {
      const errorMsg = getErrorMessage(err, 'Unknown error')
      console.error(`[TaskDetailPanel] Reset & run failed for task ${task.id}:`, err)

      if (resetSucceeded) {
        // Partial success: reset worked but execution failed
        toast.error(
          `Reset succeeded but execution failed: ${errorMsg}. Click "Run Now" to manually start the watch.`,
          { duration: 8000 }
        )
      } else {
        // Complete failure: reset failed
        toast.error(`Reset failed: ${errorMsg}`)
      }
    } finally {
      setIsResetting(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setLoading(true)
        const data = await api.getAdminExecutions<{ executions: ExecutionData[] }>({ task_id: task.id, limit: 20 })
        if (!cancelled) {
          setExecutions(data.executions ?? [])
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err, 'Failed to load executions'))
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [api, task.id, retryCount])

  return (
    <div className="bg-ink-8 border-t border-ink-6 p-4 space-y-4 overflow-hidden">
      {/* Actions */}
      <div className="flex items-center gap-2">
        <SectionLabel>Actions</SectionLabel>
        <button
          onClick={handleExecute}
          disabled={isBusy}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-ink-1 text-white text-xs font-mono hover:bg-ink-1 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isExecuting ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Play className="h-3 w-3" />
          )}
          Run Now
        </button>
        <button
          onClick={handlePauseResume}
          disabled={isBusy || task.state === 'completed'}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white border border-ink-2 text-ink-0 text-xs font-mono hover:bg-ink-7 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPauseResuming ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : task.state === 'active' ? (
            <Pause className="h-3 w-3" />
          ) : (
            <Play className="h-3 w-3" />
          )}
          {task.state === 'active' ? 'Pause' : 'Resume'}
        </button>
        <button
          onClick={() => setIsResetDialogOpen(true)}
          disabled={isBusy}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-orange-600 text-white text-xs font-mono hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          title="Delete recent history and re-run fresh"
        >
          {isResetting ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <RotateCcw className="h-3 w-3" />
          )}
          Reset & Run
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
          <p className="text-xs font-mono text-ink-2 mt-1">{task.user_email}</p>
        </div>
        <div>
          <SectionLabel>Created</SectionLabel>
          <p className="text-xs font-mono text-ink-2 mt-1">{formatTimestamp(task.created_at)}</p>
        </div>
        <div>
          <SectionLabel>State Changed</SectionLabel>
          <p className="text-xs font-mono text-ink-2 mt-1">{formatTimestamp(task.state_changed_at)}</p>
        </div>
        <div>
          <SectionLabel>Next Run</SectionLabel>
          <p className="text-xs font-mono text-ink-2 mt-1">
            {formatShortTimestamp(task.next_run)}
          </p>
        </div>
      </div>

      {/* Last Agent Response */}
      <div>
        <SectionLabel>Last Agent Response</SectionLabel>
        <div className="mt-1 p-3 bg-white border border-ink-6 text-xs font-mono text-ink-2 whitespace-pre-wrap max-h-40 overflow-y-auto">
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
            <Loader2 className="h-4 w-4 animate-spin text-ink-4" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xs font-mono text-red-600">{error}</p>
            <button
              onClick={() => setRetryCount(c => c + 1)}
              className="px-2 py-1 text-[10px] font-mono border border-ink-6 hover:border-ink-5 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : executions.length === 0 ? (
          <p className="text-xs font-mono text-ink-4 mt-1">No executions yet</p>
        ) : (
          <div className="mt-1 space-y-2">
            {executions.map((exec) => (
              <ExecutionRow key={exec.id} execution={exec} />
            ))}
          </div>
        )}
      </div>

      {/* Reset & Run Confirmation Dialog */}
      <AlertDialog open={isResetDialogOpen} onOpenChange={setIsResetDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reset & Run Watch</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the last 1 day of execution history and re-run the task fresh.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleResetAndRun}
              className="bg-orange-600 hover:bg-orange-700"
            >
              Reset & Run
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

function ExecutionRow({ execution }: { execution: ExecutionData }) {
  const confidence = typeof execution.result?.confidence === 'number' ? execution.result.confidence : undefined
  const sourceCount = Array.isArray(execution.grounding_sources) ? execution.grounding_sources.length : 0

  return (
    <div className="bg-white border border-ink-6 p-3 space-y-2">
      <div className="flex items-center gap-3 flex-wrap">
        <StatusBadge variant={stateToVariant(execution.status)} />
        <span className="text-[10px] font-mono text-ink-3 flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {formatTimestamp(execution.started_at)}
        </span>
        <span className="text-[10px] font-mono text-ink-4">
          {formatDuration(execution.started_at, execution.completed_at)}
        </span>
        {execution.notification && (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-600">
            <Zap className="h-3 w-3" />
            Notified
          </span>
        )}
        {confidence != null && (
          <span className="text-[10px] font-mono text-ink-3">
            conf: {typeof confidence === 'number' ? `${confidence}%` : String(confidence)}
          </span>
        )}
        {sourceCount > 0 && (
          <span className="text-[10px] font-mono text-ink-4 flex items-center gap-1">
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
          <summary className="cursor-pointer text-ink-4 hover:text-ink-3 transition-colors">
            Agent Reasoning
          </summary>
          <pre className="mt-1 p-2 bg-ink-8 border border-ink-6 overflow-x-auto text-ink-3 max-h-40 overflow-y-auto whitespace-pre-wrap">
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
          <summary className="cursor-pointer text-ink-4 hover:text-ink-3 transition-colors">
            Raw JSON
          </summary>
          <pre className="mt-1 p-2 bg-ink-8 border border-ink-6 overflow-x-auto text-ink-3 max-h-60 overflow-y-auto">
            {JSON.stringify(execution.result, null, 2)}
          </pre>
        </details>
      )}
    </div>
  )
}
