import { formatDistanceToNow } from 'date-fns'
import { formatDuration } from '@/lib/utils'
import { CheckCircle2, XCircle, Clock, Search, User, Link } from 'lucide-react'

interface GroundingSource {
  title: string
  uri: string
}

interface Execution {
  id: string
  status: string
  started_at: string
  completed_at: string | null
  notification: string | null
  grounding_sources: GroundingSource[]
  search_query: string
  user_email: string
}

interface ExecutionCardProps {
  execution: Execution
}

export function ExecutionCard({ execution }: ExecutionCardProps) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[9px] font-mono uppercase tracking-wider border border-emerald-200">
            <CheckCircle2 className="h-3 w-3" />
            Success
          </span>
        )
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-red-50 text-red-700 text-[9px] font-mono uppercase tracking-wider border border-red-200">
            <XCircle className="h-3 w-3" />
            Failed
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-zinc-50 text-zinc-600 text-[9px] font-mono uppercase tracking-wider border border-zinc-200">
            <Clock className="h-3 w-3" />
            {status}
          </span>
        )
    }
  }

  return (
    <div className="p-3 border border-zinc-200 hover:border-zinc-300 transition-colors">
      <div className="space-y-3">
        <div className="flex items-start gap-3">
          <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center shrink-0">
            <Search className="h-4 w-4 text-zinc-600" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-mono text-zinc-900 break-words">{execution.search_query}</p>
            <div className="flex items-center gap-1 text-[10px] font-mono text-zinc-400 mt-0.5">
              <User className="h-3 w-3" />
              <span className="truncate" title={execution.user_email}>{execution.user_email}</span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              {getStatusBadge(execution.status)}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-mono text-zinc-500">
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {execution.started_at
              ? formatDistanceToNow(new Date(execution.started_at), { addSuffix: true })
              : '-'}
          </div>
          <div>
            <span className="text-zinc-400">Duration:</span>{' '}
            <span className="text-zinc-700">
              {formatDuration(execution.started_at, execution.completed_at, '-')}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Link className="h-3 w-3" />
            <span className="text-zinc-700">{execution.grounding_sources?.length || 0}</span>
            <span className="text-zinc-400">sources</span>
          </div>
        </div>
      </div>
    </div>
  )
}
