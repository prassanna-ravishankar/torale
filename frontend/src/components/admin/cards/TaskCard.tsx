import { Search, User } from 'lucide-react'
import { StatusBadge } from '@/components/torale'
import { stateToVariant } from '../types'
import type { TaskData } from '../types'

interface TaskCardProps {
  task: TaskData
  isExpanded: boolean
  onToggle: () => void
}

export function TaskCard({ task, isExpanded, onToggle }: TaskCardProps) {
  return (
    <div
      className={`p-3 border transition-colors cursor-pointer ${isExpanded ? 'border-zinc-400 bg-zinc-50' : 'border-zinc-200 hover:border-zinc-300'}`}
      onClick={onToggle}
    >
      <div className="space-y-3">
        <div className="flex items-start gap-3">
          <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
            <Search className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-xs sm:text-sm font-grotesk font-bold text-zinc-900 truncate" title={task.name}>
              {task.name}
            </h3>
            <div className="flex items-center gap-1 text-[10px] font-mono text-zinc-400 mt-0.5">
              <User className="h-3 w-3" />
              <span className="truncate" title={task.user_email}>{task.user_email}</span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              <StatusBadge variant={stateToVariant(task.state)} />
            </div>
          </div>
        </div>

        <div className="space-y-2 pl-11">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 mb-0.5">Search Query</p>
            <p className="text-xs font-mono text-zinc-700 break-words">{task.search_query}</p>
          </div>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] font-mono text-zinc-500 pl-11">
          <div>
            <span className="text-zinc-400">Next Run:</span>{' '}
            <span className="text-zinc-700">
              {task.next_run
                ? new Date(task.next_run).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
                : '-'}
            </span>
          </div>
          <div>
            <span className="text-zinc-400">Runs:</span>{' '}
            <span className="text-zinc-700">{task.execution_count}</span>
          </div>
          <div>
            <span className="text-zinc-400">Triggers:</span>{' '}
            <span className="text-zinc-700">{task.trigger_count}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
