import { Fragment, useCallback, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { TaskCard } from './cards/TaskCard'
import { TaskDetailPanel } from './TaskDetailPanel'
import { Loader2, Search, Zap } from 'lucide-react'
import { SectionLabel, BrutalistCard, StatusBadge, BrutalistSwitch } from '@/components/torale'
import { stateToVariant } from './types'
import type { TaskData } from './types'

interface TasksTableProps {
  initialExpandedTaskId?: string | null
}

export function TasksTable({ initialExpandedTaskId }: TasksTableProps = {}) {
  const [tasks, setTasks] = useState<TaskData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeOnly, setActiveOnly] = useState(false)
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(initialExpandedTaskId || null)

  const loadTasks = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getAdminQueries({ limit: 100, active_only: activeOnly })
      setTasks(data.queries ?? [])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks')
    } finally {
      setLoading(false)
    }
  }, [activeOnly])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  const toggleExpanded = (taskId: string) => {
    setExpandedTaskId(prev => prev === taskId ? null : taskId)
  }

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
            onClick={loadTasks}
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
            <Search className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-grotesk font-bold">All Tasks</h3>
            <p className="text-[10px] font-mono text-zinc-400">
              Click a row to view task details and execution history
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <BrutalistSwitch
            checked={activeOnly}
            onCheckedChange={setActiveOnly}
          />
          <label className="text-xs font-mono text-zinc-600 whitespace-nowrap">
            Active only
          </label>
        </div>
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-200 bg-zinc-50">
              <th className="text-left p-3"><SectionLabel>User</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Name</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Search Query</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>State</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Next Run</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Executions</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Triggered</SectionLabel></th>
            </tr>
          </thead>
          <tbody>
            {tasks.length === 0 ? (
              <tr>
                <td colSpan={7} className="p-8 text-center">
                  <Search className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
                  <p className="text-xs text-zinc-500 font-mono">No tasks found</p>
                </td>
              </tr>
            ) : (
              tasks.map((task) => (
                <Fragment key={task.id}>
                  <tr
                    onClick={() => toggleExpanded(task.id)}
                    className={`border-b border-zinc-100 cursor-pointer transition-colors ${
                      expandedTaskId === task.id ? 'bg-zinc-100' : 'hover:bg-zinc-50'
                    }`}
                  >
                    <td className="p-3 text-xs font-mono text-zinc-600">{task.user_email}</td>
                    <td className="p-3 text-sm font-mono text-zinc-900">{task.name}</td>
                    <td className="p-3 text-xs font-mono text-zinc-700 max-w-xs truncate">{task.search_query}</td>
                    <td className="p-3">
                      <StatusBadge variant={stateToVariant(task.state)} />
                    </td>
                    <td className="p-3 text-xs font-mono text-zinc-600">
                      {task.next_run
                        ? new Date(task.next_run).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
                        : '-'}
                    </td>
                    <td className="p-3 text-sm font-mono text-zinc-900">{task.execution_count}</td>
                    <td className="p-3">
                      <span className="inline-flex items-center gap-1 text-sm font-mono text-emerald-600">
                        <Zap className="h-3 w-3" />
                        {task.trigger_count}
                      </span>
                    </td>
                  </tr>
                  {expandedTaskId === task.id && (
                    <tr>
                      <td colSpan={7} className="p-0">
                        <TaskDetailPanel task={task} onTaskUpdate={loadTasks} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="block md:hidden p-4 space-y-3">
        {tasks.length === 0 ? (
          <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
            <Search className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
            <p className="text-xs text-zinc-500 font-mono">No tasks found</p>
          </div>
        ) : (
          tasks.map((task) => (
            <div key={task.id}>
              <TaskCard
                task={task}
                isExpanded={expandedTaskId === task.id}
                onToggle={() => toggleExpanded(task.id)}
              />
              {expandedTaskId === task.id && (
                <TaskDetailPanel task={task} onTaskUpdate={loadTasks} />
              )}
            </div>
          ))
        )}
      </div>
    </BrutalistCard>
  )
}
