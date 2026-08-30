'use client'

import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'

import { useApi } from '@/hooks/useApi';
import type { Task } from '@/types'
import { AppShell } from '@/components/app/AppShell'
import { TaskCreationDialog } from '@/components/TaskCreationDialog'
import { TaskEditDialog } from '@/components/TaskEditDialog'
import { FirstTimeExperience } from '@/components/FirstTimeExperience'
import { WatchList } from '@/components/dashboard/WatchList'
import { useAuth } from '@/contexts/AuthContext'
import { useWelcomeFlow } from '@/hooks/useWelcomeFlow'
import { captureEvent } from '@/lib/posthog'
import { cn } from '@/lib/utils'
import landingStyles from '@/components/landing/Landing.module.css'

interface DashboardProps {
  /**
   * Called when a watch is created (passes new id + justCreated=true so the
   * detail route can poll for the first run).
   */
  onTaskClick: (taskId: string, justCreated?: boolean) => void
}

/**
 * Watch list page (formerly "Dashboard"). Single-purpose surface: the user's
 * list of active watches. No global feed tab (per brief: "the web is not a
 * feed"). Triggered moments live in each watch's detail timeline.
 *
 * Renders its own AppShell so the Sidebar gets the watches data it needs for
 * counts + Recent section. Topbar shows "Watches" crumb + "New watch →" CTA.
 */
export const Dashboard: React.FC<DashboardProps> = ({ onTaskClick }) => {
  const api = useApi()
  const { user } = useAuth()
  const { handleWelcomeComplete } = useWelcomeFlow()
  const searchParams = useSearchParams()
  const initialFilter = (searchParams?.get('filter') as 'triggered' | 'all' | null) ?? 'all'

  const [tasks, setTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [editTask, setEditTask] = useState<Task | null>(null)
  const [showWelcome, setShowWelcome] = useState(false)

  const loadTasks = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await api.getTasks()
      setTasks(data)
    } catch (error) {
      console.error('Failed to load watches:', error)
      toast.error("Couldn't load your watches")
    } finally {
      setIsLoading(false)
    }
  }, [api])

  useEffect(() => {
    void loadTasks()
  }, [loadTasks])

  useEffect(() => {
    if (user?.has_seen_welcome === false) {
      setShowWelcome(true)
    } else if (user?.has_seen_welcome === true) {
      setShowWelcome(false)
    }
  }, [user])

  const onWelcomeComplete = async () => {
    await handleWelcomeComplete()
    setShowWelcome(false)
  }

  const handleTaskCreated = (task: Task) => {
    loadTasks()
    onTaskClick(task.id, true)
    captureEvent('task_created', { task_id: task.id })
  }

  const handleTaskUpdated = (task: Task) => {
    setTasks((prev) => prev.map((t) => (t.id === task.id ? task : t)))
  }

  const handleMore = (watch: Task) => {
    setEditTask(watch)
  }

  if (showWelcome) {
    return <FirstTimeExperience onComplete={onWelcomeComplete} />
  }

  const newWatchAction = (
    <button
      type="button"
      onClick={() => setIsCreating(true)}
      className={cn(landingStyles.btn, landingStyles.btnPrimary)}
      style={{ padding: '7px 13px', fontSize: '13px' }}
    >
      <Plus size={14} strokeWidth={1.75} style={{ marginRight: '4px' }} />
      New watch
    </button>
  )

  return (
    <AppShell
      crumbs={[{ label: 'Watches' }]}
      actions={newWatchAction}
      watches={tasks}
    >
      <WatchList
        watches={tasks}
        isLoading={isLoading}
        onCreate={() => setIsCreating(true)}
        onMore={handleMore}
        initialFilter={initialFilter as 'all' | 'triggered'}
      />

      <TaskCreationDialog
        open={isCreating}
        onOpenChange={setIsCreating}
        onTaskCreated={handleTaskCreated}
      />

      {editTask && (
        <TaskEditDialog
          task={editTask}
          open={!!editTask}
          onOpenChange={(open) => !open && setEditTask(null)}
          onSuccess={handleTaskUpdated}
        />
      )}
    </AppShell>
  )
}

export default Dashboard
