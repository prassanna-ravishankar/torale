import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { ExternalLink, Loader2, Clock, Play, Pause, Calendar } from 'lucide-react'
import { formatDuration } from '@/lib/utils'
import { WorkflowCard } from './cards/WorkflowCard'
import { ScheduleCard } from './cards/ScheduleCard'
import { SectionLabel, BrutalistCard, StatusBadge } from '@/components/torale'

interface Workflow {
  workflow_id: string
  run_id: string
  workflow_type: string
  status: string
  start_time: string | null
  close_time: string | null
  execution_time: string | null
  ui_url: string
}

interface Schedule {
  schedule_id: string
  spec: string | null
  paused: boolean
  next_run: string | null
  recent_actions: number
  created_at: string | null
}

export function TemporalMonitor() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'workflows' | 'schedules'>('workflows')

  useEffect(() => {
    loadTemporalData()
  }, [])

  const loadTemporalData = async () => {
    try {
      setLoading(true)
      const [workflowsData, schedulesData] = await Promise.all([
        api.getTemporalWorkflows(),
        api.getTemporalSchedules(),
      ])
      setWorkflows(workflowsData.workflows)
      setSchedules(schedulesData.schedules)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Temporal data')
    } finally {
      setLoading(false)
    }
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
            onClick={loadTemporalData}
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
      {/* Header with Tabs */}
      <div className="border-b border-zinc-200">
        <div className="p-4 border-b border-zinc-200 flex items-center gap-3">
          <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
            <Clock className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-grotesk font-bold">Temporal Monitor</h3>
            <p className="text-[10px] font-mono text-zinc-400">
              Workflows and schedules management
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex">
          <button
            onClick={() => setActiveTab('workflows')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-xs font-mono transition-colors border-b-2 ${
              activeTab === 'workflows'
                ? 'bg-zinc-900 text-white border-zinc-900'
                : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50 border-transparent'
            }`}
          >
            <Play className="h-4 w-4" />
            Workflows ({workflows.length})
          </button>
          <button
            onClick={() => setActiveTab('schedules')}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-xs font-mono transition-colors border-b-2 ${
              activeTab === 'schedules'
                ? 'bg-zinc-900 text-white border-zinc-900'
                : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50 border-transparent'
            }`}
          >
            <Calendar className="h-4 w-4" />
            Schedules ({schedules.length})
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'workflows' ? (
        <>
          {/* Workflows - Desktop Table View */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-200 bg-zinc-50">
                  <th className="text-left p-3"><SectionLabel>Workflow ID</SectionLabel></th>
                  <th className="text-left p-3"><SectionLabel>Type</SectionLabel></th>
                  <th className="text-left p-3"><SectionLabel>Status</SectionLabel></th>
                  <th className="text-left p-3"><SectionLabel>Started</SectionLabel></th>
                  <th className="text-left p-3"><SectionLabel>Duration</SectionLabel></th>
                </tr>
              </thead>
              <tbody>
                {workflows.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-8 text-center">
                      <Play className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
                      <p className="text-xs text-zinc-500 font-mono">No recent workflows</p>
                    </td>
                  </tr>
                ) : (
                  workflows.map((workflow) => (
                    <tr key={`${workflow.workflow_id}-${workflow.run_id}`} className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors">
                      <td className="p-3">
                        <a
                          href={workflow.ui_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-mono text-zinc-900 hover:text-[hsl(10,90%,55%)] transition-colors"
                        >
                          <span className="truncate max-w-[200px]">{workflow.workflow_id}</span>
                          <ExternalLink className="h-3 w-3 flex-shrink-0" />
                        </a>
                      </td>
                      <td className="p-3 text-xs font-mono text-zinc-600">{workflow.workflow_type}</td>
                      <td className="p-3">
                        <StatusBadge variant={
                          ({
                            COMPLETED: 'completed',
                            FAILED: 'failed',
                            RUNNING: 'running',
                          } as const)[workflow.status] || 'unknown'
                        } />
                      </td>
                      <td className="p-3 text-xs font-mono text-zinc-500">
                        {workflow.start_time
                          ? formatDistanceToNow(new Date(workflow.start_time), { addSuffix: true })
                          : '-'}
                      </td>
                      <td className="p-3 text-xs font-mono text-zinc-900">
                        {formatDuration(
                          workflow.start_time,
                          workflow.close_time,
                          workflow.status === 'RUNNING' ? 'In progress' : '-'
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Workflows - Mobile Card View */}
          <div className="block md:hidden p-4 space-y-3">
            {workflows.length === 0 ? (
              <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
                <Play className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
                <p className="text-xs text-zinc-500 font-mono">No recent workflows</p>
              </div>
            ) : (
              workflows.map((workflow) => (
                <WorkflowCard key={`${workflow.workflow_id}-${workflow.run_id}`} workflow={workflow} />
              ))
            )}
          </div>
        </>
      ) : (
        <>
          {/* Schedules - Desktop Table View */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-200 bg-zinc-50">
                  <th className="text-left p-3"><SectionLabel>Schedule ID</SectionLabel></th>
                  <th className="text-left p-3"><SectionLabel>Cron Spec</SectionLabel></th>
                  <th className="text-left p-3"><SectionLabel>Status</SectionLabel></th>
                  <th className="text-left p-3"><SectionLabel>Recent Actions</SectionLabel></th>
                </tr>
              </thead>
              <tbody>
                {schedules.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center">
                      <Calendar className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
                      <p className="text-xs text-zinc-500 font-mono">No active schedules</p>
                    </td>
                  </tr>
                ) : (
                  schedules.map((schedule) => (
                    <tr key={schedule.schedule_id} className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors">
                      <td className="p-3 text-xs font-mono text-zinc-900 truncate max-w-[200px]">
                        {schedule.schedule_id}
                      </td>
                      <td className="p-3">
                        <code className="px-1.5 py-0.5 bg-zinc-100 text-zinc-700 text-[10px] font-mono">
                          {schedule.spec || 'N/A'}
                        </code>
                      </td>
                      <td className="p-3">
                        <StatusBadge variant={schedule.paused ? 'paused' : 'running'} />
                      </td>
                      <td className="p-3 text-sm font-mono text-zinc-900">{schedule.recent_actions}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Schedules - Mobile Card View */}
          <div className="block md:hidden p-4 space-y-3">
            {schedules.length === 0 ? (
              <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
                <Calendar className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
                <p className="text-xs text-zinc-500 font-mono">No active schedules</p>
              </div>
            ) : (
              schedules.map((schedule) => <ScheduleCard key={schedule.schedule_id} schedule={schedule} />)
            )}
          </div>
        </>
      )}
    </BrutalistCard>
  )
}
