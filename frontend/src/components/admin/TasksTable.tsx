import { Fragment, useCallback, useEffect, useState } from 'react'
import { formatShortDateTime, getErrorMessage } from '@/lib/utils'
import { useApi } from '@/hooks/useApi';
import { TaskCard } from './cards/TaskCard'
import { TaskDetailPanel } from './TaskDetailPanel'
import { Loader2, Search, Zap } from 'lucide-react'
import { SectionLabel, Card, StatusBadge, Switch } from '@/components/torale'
import { stateToVariant } from './types'
import type { TaskData } from './types'

interface TasksTableProps {
  initialExpandedTaskId?: string | null
}

export function TasksTable({ initialExpandedTaskId }: TasksTableProps = {}) {
  const api = useApi()
  const [tasks, setTasks] = useState<TaskData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeOnly, setActiveOnly] = useState(false)
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(initialExpandedTaskId || null)

  const loadTasks = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getAdminQueries<{ queries: TaskData[] }>({ limit: 100, active_only: activeOnly })
      setTasks(data.queries ?? [])
      setError(null)
    } catch (err) {
      setError(getErrorMessage(err, "Couldn't load your watches"))
    } finally {
      setLoading(false)
    }
  }, [activeOnly, api])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  const toggleExpanded = (taskId: string) => {
    setExpandedTaskId(prev => prev === taskId ? null : taskId)
  }

  if (loading) {
    return (
      <Card className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-ink-4" />
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-sm font-mono text-red-600">Error: {error}</p>
          <button
            onClick={loadTasks}
            className="mt-2 px-3 py-1.5 text-xs font-mono border border-ink-6 hover:border-ink-5 transition-colors"
          >
            Retry
          </button>
        </div>
      </Card>
    )
  }

  return (
    <Card>
      {/* Header */}
      <div className="p-4 border-b border-ink-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="bg-ink-1 text-white w-8 h-8 flex items-center justify-center shrink-0">
            <Search className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold">All Watches</h3>
            <p className="text-[10px] font-mono text-ink-4">
              Click a row to view watch details and execution history
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Switch
            checked={activeOnly}
            onCheckedChange={setActiveOnly}
          />
          <label className="text-xs font-mono text-ink-3 whitespace-nowrap">
            Active only
          </label>
        </div>
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full table-fixed">
          <colgroup>
            <col className="w-[15%]" />
            <col className="w-[15%]" />
            <col className="w-[25%]" />
            <col className="w-[10%]" />
            <col className="w-[13%]" />
            <col className="w-[10%]" />
            <col className="w-[12%]" />
          </colgroup>
          <thead>
            <tr className="border-b border-ink-6 bg-ink-8">
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
                  <Search className="h-5 w-5 text-ink-4 mx-auto mb-2" />
                  <p className="text-xs text-ink-3 font-mono">No watches found</p>
                </td>
              </tr>
            ) : (
              tasks.map((task) => (
                <Fragment key={task.id}>
                  <tr
                    onClick={() => toggleExpanded(task.id)}
                    className={`border-b border-ink-7 cursor-pointer transition-colors ${
                      expandedTaskId === task.id ? 'bg-ink-7' : 'hover:bg-ink-8'
                    }`}
                  >
                    <td className="p-3 text-xs font-mono text-ink-3">
                      <div className="max-w-[200px] truncate" title={task.user_email}>{task.user_email}</div>
                    </td>
                    <td className="p-3 text-sm font-mono text-ink-0">
                      <div className="max-w-[200px] truncate" title={task.name}>{task.name}</div>
                    </td>
                    <td className="p-3 text-xs font-mono text-ink-2">
                      <div className="max-w-xs truncate" title={task.search_query}>{task.search_query}</div>
                    </td>
                    <td className="p-3">
                      <StatusBadge variant={stateToVariant(task.state)} />
                    </td>
                    <td className="p-3 text-xs font-mono text-ink-3">
                      {task.next_run
                        ? formatShortDateTime(task.next_run)
                        : '-'}
                    </td>
                    <td className="p-3 text-sm font-mono text-ink-0">{task.execution_count}</td>
                    <td className="p-3">
                      <span className="inline-flex items-center gap-1 text-sm font-mono text-emerald-600">
                        <Zap className="h-3 w-3" />
                        {task.trigger_count}
                      </span>
                    </td>
                  </tr>
                  {expandedTaskId === task.id && (
                    <tr>
                      <td colSpan={7} className="p-0 overflow-hidden">
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
          <div className="p-4 bg-ink-8 border border-dashed border-ink-5 text-center">
            <Search className="h-5 w-5 text-ink-4 mx-auto mb-2" />
            <p className="text-xs text-ink-3 font-mono">No watches found</p>
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
    </Card>
  )
}
