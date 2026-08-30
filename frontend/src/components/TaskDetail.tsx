'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { toast } from 'sonner'

import { useApi } from '@/hooks/useApi'
import { ApiError } from '@/lib/api'
import type { Task, TaskExecution } from '@/types'
import { AppShell } from '@/components/app/AppShell'
import { TaskEditDialog } from '@/components/TaskEditDialog'
import { DeleteWatchDialog } from '@/components/torale'
import { ConnectorDegradationBanner } from '@/components/connectors/ConnectorDegradationBanner'
import { MomentBlock } from '@/components/watch/MomentBlock'
import { RunTimeline } from '@/components/watch/RunTimeline'
import { WebwhenMark } from '@/components/WebwhenMark'
import landingStyles from '@/components/landing/Landing.module.css'
import styles from '@/components/watch/Watch.module.css'
import { cn, formatTimeAgo, formatTimeUntil } from '@/lib/utils'
import { ownerWatchPath } from '@/lib/watchRoutes'

interface TaskDetailProps {
  taskId: string
  onBack: () => void
  onDeleted: () => void
  /** Current user's ID (if authenticated). Used to gate owner-only actions. */
  currentUserId?: string
}

/**
 * Watch detail page — single editorial flow per webwhen kit `.detail-head` +
 * `.moment` + `.runs` patterns. Drops the legacy Intelligence/Findings/Config
 * tabs in favor of: status pill + serif-italic question header, then the
 * triggered moments, then the run timeline.
 *
 * Renders its own AppShell so the topbar carries watch-specific crumbs +
 * actions (run now, pause/resume, edit, delete).
 */
export const TaskDetail: React.FC<TaskDetailProps> = ({
  taskId,
  onBack,
  onDeleted,
  currentUserId,
}) => {
  const api = useApi()
  const router = useRouter()
  const searchParams = useSearchParams()
  const isJustCreated = searchParams?.get('justCreated') === 'true'

  const [task, setTask] = useState<Task | null>(null)
  const [executions, setExecutions] = useState<TaskExecution[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [taskError, setTaskError] = useState<ApiError | null>(null)
  const [historyError, setHistoryError] = useState<ApiError | null>(null)
  const [isHistoryLoading, setIsHistoryLoading] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)

  const loadData = useCallback(
    async (skipLoadingState = false) => {
      if (!skipLoadingState) {
        setIsLoading(true)
        setIsHistoryLoading(true)
      }

      const taskRequest = api.getTask(taskId)
        .then(taskData => {
          setTask(taskData)
          setTaskError(null)
        })
        .catch(error => {
          console.error('Failed to load watch:', error)
          setTask(null)
          setTaskError(
            error instanceof ApiError ? error : new ApiError(null, "We couldn't reach webwhen."),
          )
        })

      const historyRequest = api.getTaskExecutions(taskId)
        .then(executionsData => {
          setExecutions(executionsData)
          setHistoryError(null)
        })
        .catch(error => {
          console.error('Failed to load watch history:', error)
          setHistoryError(
            error instanceof ApiError ? error : new ApiError(null, "We couldn't reach webwhen."),
          )
        })
        .finally(() => setIsHistoryLoading(false))

      await taskRequest
      if (!skipLoadingState) setIsLoading(false)
      await historyRequest
    },
    [api, taskId],
  )

  useEffect(() => {
    loadData()
  }, [loadData])

  // Auto-refresh while the just-created watch's first run is pending/running.
  useEffect(() => {
    if (!isJustCreated || !task) return
    const first = executions[0]
    const stillRunning = executions.length === 0 || (first && ['pending', 'running'].includes(first.status))
    if (!stillRunning) return
    const interval = setInterval(() => loadData(true), 3000)
    return () => clearInterval(interval)
  }, [isJustCreated, task, executions, loadData])

  const retryHistory = async () => {
    setIsHistoryLoading(true)
    try {
      setExecutions(await api.getTaskExecutions(taskId))
      setHistoryError(null)
    } catch (error) {
      setHistoryError(
        error instanceof ApiError ? error : new ApiError(null, "We couldn't reach webwhen."),
      )
    } finally {
      setIsHistoryLoading(false)
    }
  }

  const handleRunNow = async () => {
    setIsExecuting(true)
    try {
      await api.executeTask(taskId)
      toast.success('watch is checking now')
      await loadData(true)
    } catch (error) {
      console.error('Failed to run watch:', error)
      toast.error("Couldn't start the watch")
    } finally {
      setIsExecuting(false)
    }
  }

  const handleTogglePause = async () => {
    if (!task) return
    try {
      const newState = task.state === 'active' ? 'paused' : 'active'
      await api.updateTask(taskId, { state: newState })
      await loadData(true)
      toast.success(newState === 'active' ? 'watch resumed' : 'watch paused')
    } catch (error) {
      console.error('Failed to toggle watch:', error)
      toast.error("Couldn't update the watch")
    }
  }

  const handleDelete = async () => {
    try {
      await api.deleteTask(taskId)
      toast.success('watch deleted')
      onDeleted()
    } catch (error) {
      console.error('Failed to delete watch:', error)
      toast.error("Couldn't delete the watch")
    }
  }

  const handleTaskUpdated = (updated: Task) => {
    setTask(updated)
  }

  // === Derived view-model ================================================

  const isOwner = !!(task && task.user_id === currentUserId)

  const moments = useMemo(
    () =>
      executions.filter((ex) => !!(ex.notification || ex.result?.notification)),
    [executions],
  )

  const lastRun = useMemo(() => {
    const completed = executions.find((ex) => ex.completed_at)
    return completed?.completed_at || completed?.started_at || executions[0]?.started_at || null
  }, [executions])

  // Status pill: triggered if any moment exists in the most-recent run window;
  // watching when active with no fresh trigger; otherwise mirror the state.
  const hasFreshTrigger = !!(executions[0] && (executions[0].notification || executions[0].result?.notification))
  let pillLabel = 'watching'
  let pillClass: string | undefined = styles.pillWatching
  if (task) {
    if (task.state === 'paused') {
      pillLabel = 'paused'
      pillClass = undefined
    } else if (task.state === 'completed') {
      pillLabel = 'completed'
      pillClass = undefined
    } else if (hasFreshTrigger) {
      pillLabel = 'triggered'
      pillClass = styles.pillTriggered
    }
  }

  // === Render ============================================================

  if (isLoading) {
    return (
      <AppShell crumbs={[{ label: 'Watches', href: '/dashboard' }, { label: 'watch' }]}>
        <div className={styles.loading}>loading watch…</div>
      </AppShell>
    )
  }

  if (!task) {
    const status = taskError?.status
    const title = status === 404
      ? 'watch not found'
      : status === 403
        ? 'you don’t have access to this watch'
        : status === 401
          ? 'your session has expired'
          : 'this watch couldn’t load'
    const canRetry = status !== 404 && status !== 403 && status !== 401

    return (
      <AppShell crumbs={[{ label: 'Watches', href: '/dashboard' }, { label: 'watch' }]}>
        <section className={styles.errorState} aria-live="polite">
          <h1>{title}</h1>
          <p>
            {status === 404
              ? 'It may have been deleted, made private, or the link may be incorrect.'
              : status === 401
                ? 'Sign in again to continue to your watches.'
                : taskError?.detail || 'Please try again in a moment.'}
          </p>
          <div className={styles.errorActions}>
            {canRetry && (
              <button type="button" className={cn(landingStyles.btn, landingStyles.btnPrimary)} onClick={() => void loadData()}>
                try again
              </button>
            )}
            {status === 401 ? (
              <button type="button" className={cn(landingStyles.btn, landingStyles.btnPrimary)} onClick={() => router.push(`/sign-in?redirect_url=${encodeURIComponent(ownerWatchPath(taskId))}`)}>
                sign in again
              </button>
            ) : (
              <button type="button" className={cn(landingStyles.btn, landingStyles.btnSecondary)} onClick={onBack}>
                back to watches
              </button>
            )}
          </div>
        </section>
      </AppShell>
    )
  }

  const ghostBtn = cn(landingStyles.btn, landingStyles.btnGhost)
  const ghostBtnStyle = { padding: '7px 13px', fontSize: '13px' } as const

  const actions = isOwner ? (
    <>
      <button
        type="button"
        className={ghostBtn}
        style={ghostBtnStyle}
        onClick={handleRunNow}
        disabled={isExecuting}
      >
        {isExecuting ? 'running…' : 'run now'}
      </button>
      <button
        type="button"
        className={ghostBtn}
        style={ghostBtnStyle}
        onClick={handleTogglePause}
      >
        {task.state === 'paused' ? 'resume' : 'pause'}
      </button>
      <button
        type="button"
        className={ghostBtn}
        style={ghostBtnStyle}
        onClick={() => setIsEditOpen(true)}
      >
        edit
      </button>
      <button
        type="button"
        className={ghostBtn}
        style={ghostBtnStyle}
        onClick={() => setIsDeleteOpen(true)}
      >
        delete
      </button>
    </>
  ) : (
    <button
      type="button"
      className={ghostBtn}
      style={ghostBtnStyle}
      onClick={async () => {
        try {
          const forked = await api.forkTask(taskId)
          toast.success('copied to your watches')
          router.push(`${ownerWatchPath(forked.id)}?justCreated=true`)
        } catch (error) {
          console.error('Failed to fork watch:', error)
          toast.error("Couldn't copy the watch")
        }
      }}
    >
      copy this watch
    </button>
  )

  return (
    <AppShell
      crumbs={[
        { label: 'Watches', href: '/dashboard' },
        { label: task.name || 'watch' },
      ]}
      actions={actions}
    >
      {/* Public-watch RSS alternate is set by the surrounding page (server
          component) via Next metadata so it lands in the static HTML head
          before hydration. The Helmet that used to live here served the
          same purpose under Vite. */}

      {isOwner && (
        <ConnectorDegradationBanner attachedSlugs={task.attached_connector_slugs ?? []} />
      )}

      <header className={styles.detailHead}>
        <div className={styles.left}>
          <div className={styles.pillRow}>
            {hasFreshTrigger && (
              <WebwhenMark animated="triggered" size={20} title="triggered" />
            )}
            <span className={cn(styles.pill, pillClass)}>{pillLabel}</span>
          </div>
          <h1 className={styles.question}>{task.condition_description}</h1>
          <div className={styles.meta}>
            {lastRun && (
              <span>
                <strong>checked</strong> {formatTimeAgo(lastRun)}
              </span>
            )}
            {task.next_run && (
              <span>
                <strong>next</strong> {formatTimeUntil(task.next_run)}
              </span>
            )}
            <span>
              <strong>runs</strong> {executions.length}
            </span>
            {task.is_public && (
              <span>
                <strong>views</strong> {task.view_count}
              </span>
            )}
          </div>
        </div>
      </header>

      {moments.length > 0 && (
        <>
          <h2 className={styles.sectionH}>the moments</h2>
          {moments.map((m) => (
            <MomentBlock key={m.id} execution={m} />
          ))}
        </>
      )}

      <h2 className={styles.sectionH}>recent runs</h2>
      {isHistoryLoading && !historyError && (
        <div className={styles.historyLoading}>loading recent runs…</div>
      )}
      {historyError && (
        <div className={styles.historyError} role="status">
          <span>recent runs couldn’t load</span>
          <button type="button" onClick={() => void retryHistory()} disabled={isHistoryLoading}>
            {isHistoryLoading ? 'trying…' : 'try again'}
          </button>
        </div>
      )}
      {!isHistoryLoading && <RunTimeline executions={executions} />}

      <TaskEditDialog
        task={task}
        open={isEditOpen}
        onOpenChange={setIsEditOpen}
        onSuccess={handleTaskUpdated}
      />

      <DeleteWatchDialog
        taskName={task.name}
        open={isDeleteOpen}
        onOpenChange={setIsDeleteOpen}
        onConfirm={handleDelete}
        extraDescription="all run history will be permanently deleted."
      />
    </AppShell>
  )
}

export default TaskDetail
