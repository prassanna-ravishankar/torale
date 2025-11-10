import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

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
    <Card className="p-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="font-mono text-xs truncate">{schedule.schedule_id}</p>
            <p className="font-mono text-xs text-muted-foreground mt-1">
              {schedule.spec || 'N/A'}
            </p>
          </div>
          <Badge
            variant={schedule.paused ? 'secondary' : 'default'}
            className="text-xs flex-shrink-0"
          >
            {schedule.paused ? 'Paused' : 'Running'}
          </Badge>
        </div>

        <div className="text-xs text-muted-foreground">
          <span className="font-medium">Recent Actions:</span>{' '}
          {schedule.recent_actions}
        </div>
      </div>
    </Card>
  )
}
