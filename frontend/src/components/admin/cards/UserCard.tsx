import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatDistanceToNow } from 'date-fns'

interface User {
  id: string
  email: string
  is_active: boolean
  created_at: string
  task_count: number
  total_executions: number
  conditions_met_count: number
}

interface UserCardProps {
  user: User
  onDeactivate: (userId: string, email: string) => void
}

export function UserCard({ user, onDeactivate }: UserCardProps) {
  return (
    <Card className="p-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="font-medium text-sm truncate" title={user.email}>{user.email}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Joined {user.created_at
                ? formatDistanceToNow(new Date(user.created_at), { addSuffix: true })
                : '-'}
            </p>
          </div>
          <Badge
            variant={user.is_active ? 'default' : 'secondary'}
            className="text-xs flex-shrink-0"
          >
            {user.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>

        <div className="grid grid-cols-3 gap-2 text-xs">
          <div>
            <p className="text-muted-foreground">Tasks</p>
            <p className="font-medium">{user.task_count}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Executions</p>
            <p className="font-medium">{user.total_executions}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Triggered</p>
            <p className="font-medium">{user.conditions_met_count}</p>
          </div>
        </div>

        {user.is_active && (
          <Button
            variant="destructive"
            size="sm"
            className="w-full min-h-[44px]"
            onClick={() => onDeactivate(user.id, user.email)}
          >
            Deactivate User
          </Button>
        )}
      </div>
    </Card>
  )
}
