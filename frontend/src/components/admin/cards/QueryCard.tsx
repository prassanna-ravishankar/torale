import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

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
    <Card className="p-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-medium text-sm truncate">{query.name}</h3>
            <p className="text-xs text-muted-foreground font-mono truncate">{query.user_email}</p>
          </div>
          <div className="flex gap-1 flex-shrink-0">
            <Badge variant={query.is_active ? 'default' : 'secondary'} className="text-xs">
              {query.is_active ? 'Active' : 'Inactive'}
            </Badge>
            {query.condition_met && (
              <Badge variant="outline" className="text-green-600 text-xs">
                Met
              </Badge>
            )}
          </div>
        </div>

        <div className="space-y-2">
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Search Query</p>
            <p className="text-sm break-words">{query.search_query}</p>
          </div>

          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Condition</p>
            <p className="text-sm text-muted-foreground break-words">{query.condition_description}</p>
          </div>

          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
            <div>
              <span className="text-muted-foreground">Schedule:</span>{' '}
              <span className="font-mono">{query.schedule}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Executions:</span>{' '}
              <span className="font-medium">{query.execution_count}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Triggered:</span>{' '}
              <span className="font-medium">{query.trigger_count}</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
