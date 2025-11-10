import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { toast } from 'sonner'

interface User {
  id: string
  email: string
  clerk_user_id: string
  is_active: boolean
  created_at: string
  task_count: number
  total_executions: number
  conditions_met_count: number
}

interface UsersData {
  users: User[]
  capacity: {
    used: number
    total: number
    available: number
  }
}

export function UsersTable() {
  const [data, setData] = useState<UsersData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      setLoading(true)
      const usersData = await api.getAdminUsers()
      setData(usersData)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const handleDeactivate = async (userId: string, email: string) => {
    if (!confirm(`Are you sure you want to deactivate user ${email}? This will free up a seat.`)) {
      return
    }

    try {
      await api.deactivateUser(userId)
      toast.success(`User ${email} has been deactivated`)
      loadUsers() // Reload the list
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to deactivate user')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading users...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-destructive">Error: {error}</div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">Platform Capacity</CardTitle>
          <CardDescription className="text-sm">
            {data.capacity.used} / {data.capacity.total} seats used • {data.capacity.available} available
          </CardDescription>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg sm:text-xl">All Users</CardTitle>
          <CardDescription className="text-sm">Manage platform users and view their activity</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Desktop Table View */}
          <div className="hidden md:block">
            <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead>Tasks</TableHead>
                <TableHead>Executions</TableHead>
                <TableHead>Triggered</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.users.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground">
                    No users found
                  </TableCell>
                </TableRow>
              ) : (
                data.users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">{user.email}</TableCell>
                    <TableCell>
                      <Badge variant={user.is_active ? 'default' : 'secondary'}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs">
                      {user.created_at
                        ? formatDistanceToNow(new Date(user.created_at), { addSuffix: true })
                        : '-'}
                    </TableCell>
                    <TableCell>{user.task_count}</TableCell>
                    <TableCell>{user.total_executions}</TableCell>
                    <TableCell>{user.conditions_met_count}</TableCell>
                    <TableCell>
                      {user.is_active && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeactivate(user.id, user.email)}
                        >
                          Deactivate
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
          </div>

          {/* Mobile Card View */}
          <div className="block md:hidden space-y-4">
            {data.users.length === 0 ? (
              <p className="text-center text-sm text-muted-foreground py-8">No users found</p>
            ) : (
              data.users.map((user) => (
                <Card key={user.id} className="p-4">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="font-medium text-sm truncate">{user.email}</p>
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
                        onClick={() => handleDeactivate(user.id, user.email)}
                      >
                        Deactivate User
                      </Button>
                    )}
                  </div>
                </Card>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
