import { CronDisplay } from '@/components/ui/CronDisplay'
import { Search, CheckCircle2, Play, Pause, User } from 'lucide-react'

interface Query {
  id: string
  name: string
  search_query: string
  condition_description: string
  schedule: string
  is_active: boolean
  condition_met: boolean
  user_email: string
  execution_count: number
  trigger_count: number
}

interface QueryCardProps {
  query: Query
}

export function QueryCard({ query }: QueryCardProps) {
  return (
    <div className="p-3 border border-zinc-200 hover:border-zinc-300 transition-colors">
      <div className="space-y-3">
        <div className="flex items-start gap-3">
          <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
            <Search className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-xs sm:text-sm font-grotesk font-bold text-zinc-900 truncate" title={query.name}>
              {query.name}
            </h3>
            <div className="flex items-center gap-1 text-[10px] font-mono text-zinc-400 mt-0.5">
              <User className="h-3 w-3" />
              <span className="truncate" title={query.user_email}>{query.user_email}</span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              {query.is_active ? (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[9px] font-mono uppercase tracking-wider border border-emerald-200">
                  <Play className="h-3 w-3" />
                  Active
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-zinc-100 text-zinc-500 text-[9px] font-mono uppercase tracking-wider border border-zinc-200">
                  <Pause className="h-3 w-3" />
                  Inactive
                </span>
              )}
              {query.condition_met && (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[9px] font-mono uppercase tracking-wider border border-emerald-200">
                  <CheckCircle2 className="h-3 w-3" />
                  Met
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-2 pl-11">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 mb-0.5">Search Query</p>
            <p className="text-xs font-mono text-zinc-700 break-words">{query.search_query}</p>
          </div>

          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 mb-0.5">Condition</p>
            <p className="text-xs font-mono text-zinc-500 break-words">{query.condition_description}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-mono text-zinc-500 pl-11">
          <div>
            <span className="text-zinc-400">Schedule:</span>{' '}
            <CronDisplay cron={query.schedule} showRaw={false} className="text-xs text-zinc-700" />
          </div>
          <div>
            <span className="text-zinc-400">Runs:</span>{' '}
            <span className="text-zinc-700">{query.execution_count}</span>
          </div>
          <div>
            <span className="text-zinc-400">Triggers:</span>{' '}
            <span className="text-zinc-700">{query.trigger_count}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
