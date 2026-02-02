import { useCallback, useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { Loader2, Clock, Calendar } from 'lucide-react'
import { SectionLabel, BrutalistCard, StatusBadge } from '@/components/torale'

interface SchedulerJob {
  id: string
  name: string
  next_run_time: string | null
  paused: boolean
  trigger: string | null
}

interface SchedulerJobsResponse {
  jobs: SchedulerJob[]
  total: number
}

function formatNextRun(nextRunTime: string | null): string {
  if (!nextRunTime) return '-'
  const date = new Date(nextRunTime)
  if (isNaN(date.getTime())) return 'Invalid date'
  return formatDistanceToNow(date, { addSuffix: true })
}

export function SchedulerMonitor() {
  const [jobs, setJobs] = useState<SchedulerJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadSchedulerData = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getSchedulerJobs()
      if (!data?.jobs || !Array.isArray(data.jobs)) {
        throw new Error('Unexpected response format from scheduler jobs endpoint')
      }
      setJobs(data.jobs as SchedulerJob[])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scheduler data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSchedulerData()
  }, [loadSchedulerData])

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
            onClick={loadSchedulerData}
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
      <div className="p-4 border-b border-zinc-200 flex items-center gap-3">
        <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
          <Clock className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-sm font-grotesk font-bold">Scheduler Monitor</h3>
          <p className="text-[10px] font-mono text-zinc-400">
            APScheduler jobs ({jobs.length})
          </p>
        </div>
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-200 bg-zinc-50">
              <th className="text-left p-3"><SectionLabel>Job ID</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Name</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Trigger</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Status</SectionLabel></th>
              <th className="text-left p-3"><SectionLabel>Next Run</SectionLabel></th>
            </tr>
          </thead>
          <tbody>
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-8 text-center">
                  <Calendar className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
                  <p className="text-xs text-zinc-500 font-mono">No scheduled jobs</p>
                </td>
              </tr>
            ) : (
              jobs.map((job) => (
                <tr key={job.id} className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors">
                  <td className="p-3 text-xs font-mono text-zinc-900 truncate max-w-[200px]">
                    {job.id}
                  </td>
                  <td className="p-3 text-xs font-mono text-zinc-600">{job.name}</td>
                  <td className="p-3">
                    <code className="px-1.5 py-0.5 bg-zinc-100 text-zinc-700 text-[10px] font-mono">
                      {job.trigger || 'N/A'}
                    </code>
                  </td>
                  <td className="p-3">
                    <StatusBadge variant={job.paused ? 'paused' : 'running'} />
                  </td>
                  <td className="p-3 text-xs font-mono text-zinc-500">
                    {formatNextRun(job.next_run_time)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="block md:hidden p-4 space-y-3">
        {jobs.length === 0 ? (
          <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
            <Calendar className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
            <p className="text-xs text-zinc-500 font-mono">No scheduled jobs</p>
          </div>
        ) : (
          jobs.map((job) => (
            <div key={job.id} className="p-3 border border-zinc-200 hover:border-zinc-300 transition-colors">
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-mono text-zinc-900 truncate" title={job.id}>
                      {job.id}
                    </p>
                    <p className="text-[10px] font-mono text-zinc-500 mt-0.5">{job.name}</p>
                  </div>
                  <StatusBadge variant={job.paused ? 'paused' : 'running'} />
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-mono text-zinc-500">
                  <div>
                    <span className="text-zinc-400">Trigger:</span>{' '}
                    <code className="px-1 py-0.5 bg-zinc-100 text-zinc-700">{job.trigger || 'N/A'}</code>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatNextRun(job.next_run_time)}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </BrutalistCard>
  )
}
