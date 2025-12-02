import { Play, Pause } from 'lucide-react'

interface Schedule {
  schedule_id: string
  spec: string | null
  paused: boolean
  recent_actions: number
}

interface ScheduleCardProps {
  schedule: Schedule
}

export function ScheduleCard({ schedule }: ScheduleCardProps) {
  return (
    <div className="p-3 border border-zinc-200 hover:border-zinc-300 transition-colors">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-mono text-zinc-900 truncate" title={schedule.schedule_id}>
              {schedule.schedule_id}
            </p>
            <code className="inline-block mt-1 px-1.5 py-0.5 bg-zinc-100 text-zinc-700 text-[10px] font-mono">
              {schedule.spec || 'N/A'}
            </code>
          </div>
          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-mono uppercase tracking-wider border ${
            schedule.paused
              ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-emerald-50 text-emerald-700 border-emerald-200'
          }`}>
            {schedule.paused ? (
              <>
                <Pause className="h-3 w-3" />
                Paused
              </>
            ) : (
              <>
                <Play className="h-3 w-3" />
                Running
              </>
            )}
          </span>
        </div>

        <div className="text-[10px] font-mono text-zinc-500">
          <span className="text-zinc-400">Recent Actions:</span>{' '}
          <span className="text-zinc-700">{schedule.recent_actions}</span>
        </div>
      </div>
    </div>
  )
}
