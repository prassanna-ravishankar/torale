import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { formatDistanceToNow } from 'date-fns'
import { Edit } from 'lucide-react'

interface User {
  id: string
  email: string
  clerk_user_id: string
  is_active: boolean
  created_at: string
  task_count: number
  total_executions: number
  conditions_met_count: number
  role?: string | null
}

interface UserCardProps {
  user: User
  currentUserClerkId?: string
  onDeactivate: (userId: string, email: string) => void
  onEditRole: (user: User) => void
}

export function UserCard({ user, currentUserClerkId, onDeactivate, onEditRole }: UserCardProps) {
  const getRoleBadgeVariant = (role?: string | null) => {
    if (role === 'admin') return 'destructive'
    if (role === 'developer') return 'default'
    return 'outline'
  }

  const getRoleDisplay = (role?: string | null) => {
    if (!role) return 'User'
    return role.charAt(0).toUpperCase() + role.slice(1)
  }

  const isCurrentUser = currentUserClerkId && user.clerk_user_id === currentUserClerkId

  return (
    <Card className="p-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="font-medium text-sm truncate" title={user.email}>{user.email}</p>
              {isCurrentUser && (
                <Badge variant="outline" className="text-xs">You</Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Joined {user.created_at
                ? formatDistanceToNow(new Date(user.created_at), { addSuffix: true })
                : '-'}
            </p>
          </div>
          <div className="flex flex-col gap-1 items-end flex-shrink-0">
            <Badge
              variant={user.is_active ? 'default' : 'secondary'}
              className="text-xs"
            >
              {user.is_active ? 'Active' : 'Inactive'}
            </Badge>
            <Badge variant={getRoleBadgeVariant(user.role)} className="text-xs">
              {getRoleDisplay(user.role)}
            </Badge>
          </div>
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

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 min-h-[44px]"
            onClick={() => onEditRole(user)}
            disabled={isCurrentUser}
          >
            <Edit className="h-4 w-4 mr-1" />
            Edit Role
          </Button>
          {user.is_active && (
            <Button
              variant="destructive"
              size="sm"
              className="flex-1 min-h-[44px]"
              onClick={() => onDeactivate(user.id, user.email)}
            >
              Deactivate
            </Button>
          )}
        </div>
      </div>
    </Card>
  )
}
