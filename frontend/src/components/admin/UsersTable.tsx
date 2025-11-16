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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {  Checkbox } from '@/components/ui/checkbox'
import { api } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { toast } from 'sonner'
import { UserCard } from './cards/UserCard'
import { Edit, UserCog, X } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

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

interface UsersData {
  users: User[]
  capacity: {
    used: number
    total: number
    available: number
  }
}

export function UsersTable() {
  const { user: currentUser } = useAuth()
  const [data, setData] = useState<UsersData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Single user role edit state
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [selectedRole, setSelectedRole] = useState<string>('')
  const [isUpdating, setIsUpdating] = useState(false)

  // Bulk edit state
  const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(new Set())
  const [showBulkDialog, setShowBulkDialog] = useState(false)
  const [bulkRole, setBulkRole] = useState<string>('')
  const [isBulkUpdating, setIsBulkUpdating] = useState(false)

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

  const handleEditRole = (user: User) => {
    // Prevent editing own role
    if (currentUser && user.clerk_user_id === currentUser.id) {
      toast.error('You cannot change your own role')
      return
    }

    setEditingUser(user)
    setSelectedRole(user.role || 'none')
  }

  const handleUpdateRole = async () => {
    if (!editingUser) return

    const roleValue = selectedRole === 'none' ? null : selectedRole

    if (!confirm(`Update role for ${editingUser.email} to ${roleValue || 'No Role'}?`)) {
      return
    }

    setIsUpdating(true)
    try {
      await api.updateUserRole(editingUser.id, roleValue)
      toast.success(`Role updated for ${editingUser.email}`)
      setEditingUser(null)
      loadUsers() // Reload to show updated role
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update role')
    } finally {
      setIsUpdating(false)
    }
  }

  const toggleUserSelection = (userId: string) => {
    const newSelection = new Set(selectedUserIds)
    if (newSelection.has(userId)) {
      newSelection.delete(userId)
    } else {
      newSelection.add(userId)
    }
    setSelectedUserIds(newSelection)
  }

  const toggleSelectAll = () => {
    if (!data) return

    // Filter out current user from selection
    const selectableUsers = data.users.filter(
      u => !currentUser || u.clerk_user_id !== currentUser.id
    )

    if (selectedUserIds.size === selectableUsers.length) {
      // Deselect all
      setSelectedUserIds(new Set())
    } else {
      // Select all selectable users
      setSelectedUserIds(new Set(selectableUsers.map(u => u.id)))
    }
  }

  const handleBulkRoleUpdate = async () => {
    if (selectedUserIds.size === 0) {
      toast.error('No users selected')
      return
    }

    const roleValue = bulkRole === 'none' ? null : bulkRole
    const selectedUsers = data?.users.filter(u => selectedUserIds.has(u.id)) || []

    if (!confirm(
      `Update role to ${roleValue || 'No Role'} for ${selectedUserIds.size} user(s)?\n\n` +
      selectedUsers.map(u => `• ${u.email}`).join('\n')
    )) {
      return
    }

    setIsBulkUpdating(true)

    try {
      // Use bulk update endpoint for better performance
      const result = await api.bulkUpdateUserRoles(Array.from(selectedUserIds), roleValue)

      setIsBulkUpdating(false)
      setShowBulkDialog(false)
      setSelectedUserIds(new Set())
      setBulkRole('')

      if (result.updated > 0) {
        toast.success(`Updated ${result.updated} user(s)`)
      }
      if (result.failed > 0) {
        toast.error(`Failed to update ${result.failed} user(s)`)
        if (result.errors.length > 0) {
          console.error('Bulk update errors:', result.errors)
        }
      }

      loadUsers() // Reload to show updated roles
    } catch (err) {
      setIsBulkUpdating(false)
      toast.error(err instanceof Error ? err.message : 'Failed to update roles')
    }
  }

  const getRoleBadgeVariant = (role?: string | null) => {
    if (role === 'admin') return 'destructive'
    if (role === 'developer') return 'default'
    return 'outline'
  }

  const getRoleDisplay = (role?: string | null) => {
    if (!role) return 'User'
    return role.charAt(0).toUpperCase() + role.slice(1)
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

  const selectableUsers = data.users.filter(
    u => !currentUser || u.clerk_user_id !== currentUser.id
  )
  const allSelected = selectedUserIds.size === selectableUsers.length && selectableUsers.length > 0

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

      {/* Bulk Actions Toolbar */}
      {selectedUserIds.size > 0 && (
        <Card className="bg-muted/50 border-primary">
          <CardHeader className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <UserCog className="h-5 w-5 text-primary" />
                <div>
                  <CardTitle className="text-sm font-medium">
                    {selectedUserIds.size} user(s) selected
                  </CardTitle>
                  <CardDescription className="text-xs">
                    Bulk actions available
                  </CardDescription>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setShowBulkDialog(true)}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Change Roles
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedUserIds(new Set())}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>
      )}

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
                <TableHead className="w-12">
                  <Checkbox
                    checked={allSelected}
                    onCheckedChange={toggleSelectAll}
                    aria-label="Select all users"
                  />
                </TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
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
                  <TableCell colSpan={9} className="text-center text-muted-foreground">
                    No users found
                  </TableCell>
                </TableRow>
              ) : (
                data.users.map((user) => {
                  const isCurrentUser = currentUser && user.clerk_user_id === currentUser.id
                  return (
                    <TableRow key={user.id}>
                      <TableCell>
                        {!isCurrentUser && (
                          <Checkbox
                            checked={selectedUserIds.has(user.id)}
                            onCheckedChange={() => toggleUserSelection(user.id)}
                            aria-label={`Select ${user.email}`}
                          />
                        )}
                      </TableCell>
                      <TableCell className="font-medium">
                        {user.email}
                        {isCurrentUser && (
                          <Badge variant="outline" className="ml-2 text-xs">You</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getRoleBadgeVariant(user.role)}>
                          {getRoleDisplay(user.role)}
                        </Badge>
                      </TableCell>
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
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEditRole(user)}
                            disabled={isCurrentUser}
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            Role
                          </Button>
                          {user.is_active && (
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDeactivate(user.id, user.email)}
                            >
                              Deactivate
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })
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
                <UserCard
                  key={user.id}
                  user={user}
                  currentUserClerkId={currentUser?.id}
                  onDeactivate={handleDeactivate}
                  onEditRole={handleEditRole}
                />
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Single User Role Edit Dialog */}
      <Dialog open={!!editingUser} onOpenChange={() => setEditingUser(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User Role</DialogTitle>
            <DialogDescription>
              Change the role for {editingUser?.email}
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Select value={selectedRole} onValueChange={setSelectedRole}>
              <SelectTrigger>
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No Role (Regular User)</SelectItem>
                <SelectItem value="developer">Developer</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingUser(null)} disabled={isUpdating}>
              Cancel
            </Button>
            <Button onClick={handleUpdateRole} disabled={isUpdating}>
              {isUpdating ? 'Updating...' : 'Update Role'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Role Edit Dialog */}
      <Dialog open={showBulkDialog} onOpenChange={setShowBulkDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk Update Roles</DialogTitle>
            <DialogDescription>
              Change the role for {selectedUserIds.size} selected user(s)
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            <Select value={bulkRole} onValueChange={setBulkRole}>
              <SelectTrigger>
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No Role (Regular User)</SelectItem>
                <SelectItem value="developer">Developer</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
              </SelectContent>
            </Select>
            <div className="text-sm text-muted-foreground">
              Selected users:
              <ul className="mt-2 space-y-1">
                {data?.users
                  .filter(u => selectedUserIds.has(u.id))
                  .map(u => (
                    <li key={u.id} className="font-mono text-xs">• {u.email}</li>
                  ))}
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBulkDialog(false)} disabled={isBulkUpdating}>
              Cancel
            </Button>
            <Button onClick={handleBulkRoleUpdate} disabled={isBulkUpdating || !bulkRole}>
              {isBulkUpdating ? 'Updating...' : 'Update Roles'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
