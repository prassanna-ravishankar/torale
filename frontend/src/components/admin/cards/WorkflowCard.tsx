import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ExternalLink } from 'lucide-react'
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
  return (
    <Card className="p-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <a
              href={workflow.ui_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-primary hover:underline"
            >
              <span className="font-mono text-xs truncate" title={workflow.workflow_id}>{workflow.workflow_id}</span>
              <ExternalLink className="h-3 w-3 flex-shrink-0" />
            </a>
            <p className="text-sm text-muted-foreground mt-1">{workflow.workflow_type}</p>
          </div>
          <Badge
            variant={
              workflow.status === 'COMPLETED'
                ? 'default'
                : workflow.status === 'FAILED'
                  ? 'destructive'
                  : 'secondary'
            }
            className="text-xs flex-shrink-0"
          >
            {workflow.status}
          </Badge>
        </div>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
          <div>
            <span className="font-medium">Started:</span>{' '}
            {workflow.start_time
              ? formatDistanceToNow(new Date(workflow.start_time), { addSuffix: true })
              : '-'}
          </div>
          <div>
            <span className="font-medium">Duration:</span>{' '}
            {formatDuration(
              workflow.start_time,
              workflow.close_time,
              workflow.status === 'RUNNING' ? 'In progress' : '-'
            )}
          </div>
        </div>
      </div>
    </Card>
  )
}
