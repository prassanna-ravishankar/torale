import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatDistanceToNow } from 'date-fns'
import { formatDuration } from '@/lib/utils'

interface GroundingSource {
  title: string
  uri: string
}

interface Execution {
  id: string
  status: string
  started_at: string
  completed_at: string | null
  condition_met: boolean | null
  grounding_sources: GroundingSource[]
  search_query: string
  user_email: string
}

interface ExecutionCardProps {
  execution: Execution
}

export function ExecutionCard({ execution }: ExecutionCardProps) {
  return (
    <Card className="p-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium break-words">{execution.search_query}</p>
            <p className="text-xs text-muted-foreground font-mono truncate mt-0.5" title={execution.user_email}>{execution.user_email}</p>
          </div>
          <Badge
            variant={
              execution.status === 'success'
                ? 'default'
                : execution.status === 'failed'
                  ? 'destructive'
                  : 'secondary'
            }
            className="text-xs flex-shrink-0"
          >
            {execution.status}
          </Badge>
        </div>

        <div className="flex flex-wrap gap-2">
          {execution.condition_met !== null && (
            <div>
              <span className="text-xs text-muted-foreground">Condition: </span>
              <Badge variant={execution.condition_met ? 'default' : 'outline'} className="text-xs">
                {execution.condition_met ? 'Met' : 'Not met'}
              </Badge>
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <div>
            <span className="font-medium">Started:</span>{' '}
            {execution.started_at
              ? formatDistanceToNow(new Date(execution.started_at), { addSuffix: true })
              : '-'}
          </div>
          <div>
            <span className="font-medium">Duration:</span>{' '}
            {formatDuration(execution.started_at, execution.completed_at, '-')}
          </div>
          <div>
            <span className="font-medium">Sources:</span>{' '}
            {execution.grounding_sources?.length || 0}
          </div>
        </div>
      </div>
    </Card>
  )
}
