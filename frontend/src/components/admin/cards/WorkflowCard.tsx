import { ExternalLink, CheckCircle2, XCircle, RefreshCw, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { formatDuration } from '@/lib/utils'

interface Workflow {
  workflow_id: string
  run_id: string
  workflow_type: string
  status: string
  start_time: string | null
  close_time: string | null
  ui_url: string
}

interface WorkflowCardProps {
  workflow: Workflow
}

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[9px] font-mono uppercase tracking-wider border border-emerald-200">
            <CheckCircle2 className="h-3 w-3" />
            Completed
          </span>
        )
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-red-50 text-red-700 text-[9px] font-mono uppercase tracking-wider border border-red-200">
            <XCircle className="h-3 w-3" />
            Failed
          </span>
        )
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-50 text-blue-700 text-[9px] font-mono uppercase tracking-wider border border-blue-200">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Running
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center px-1.5 py-0.5 bg-zinc-50 text-zinc-600 text-[9px] font-mono uppercase tracking-wider border border-zinc-200">
            {status}
          </span>
        )
    }
  }

  return (
    <div className="p-3 border border-zinc-200 hover:border-zinc-300 transition-colors">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <a
              href={workflow.ui_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs font-mono text-zinc-900 hover:text-[hsl(10,90%,55%)] transition-colors"
            >
              <span className="truncate" title={workflow.workflow_id}>{workflow.workflow_id}</span>
              <ExternalLink className="h-3 w-3 flex-shrink-0" />
            </a>
            <p className="text-[10px] font-mono text-zinc-500 mt-0.5">{workflow.workflow_type}</p>
          </div>
          {getStatusBadge(workflow.status)}
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-mono text-zinc-500">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {workflow.start_time
              ? formatDistanceToNow(new Date(workflow.start_time), { addSuffix: true })
              : '-'}
          </div>
          <div>
            <span className="text-zinc-400">Duration:</span>{' '}
            <span className="text-zinc-700">
              {formatDuration(
                workflow.start_time,
                workflow.close_time,
                workflow.status === 'RUNNING' ? 'In progress' : '-'
              )}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
