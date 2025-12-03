import { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { api } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { toast } from 'sonner'
import { UserCard } from './cards/UserCard'
import {
  Loader2,
  Users,
  Edit,
  UserCog,
  X,
  ChevronDown,
  CheckCircle2,
  Shield,
  Code2,
  User,
  ListChecks,
  Activity,
  Zap,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { SectionLabel, BrutalistCard, StatusBadge } from '@/components/torale'

interface UserData {
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

interface UsersDataResponse {
  users: UserData[]
  capacity: {
    used: number
    total: number
    available: number
  }
}

export function UsersTable() {
  const { user: currentUser } = useAuth()
  const [data, setData] = useState<UsersDataResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Single user role edit state
  const [editingUser, setEditingUser] = useState<UserData | null>(null)
  const [selectedRole, setSelectedRole] = useState<string>('')
  const [isUpdating, setIsUpdating] = useState(false)
  const [showRoleDropdown, setShowRoleDropdown] = useState(false)

  // Bulk edit state
  const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(new Set())
  const [showBulkDialog, setShowBulkDialog] = useState(false)
  const [bulkRole, setBulkRole] = useState<string>('')
  const [isBulkUpdating, setIsBulkUpdating] = useState(false)
  const [showBulkRoleDropdown, setShowBulkRoleDropdown] = useState(false)

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
      loadUsers()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to deactivate user')
    }
  }

  const handleEditRole = (user: UserData) => {
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

    setIsUpdating(true)
    try {
      await api.updateUserRole(editingUser.id, roleValue)
      toast.success(`Role updated for ${editingUser.email}`)
      setEditingUser(null)
      loadUsers()
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

    const selectableUsers = data.users.filter(
      u => !currentUser || u.clerk_user_id !== currentUser.id
    )

    if (selectedUserIds.size === selectableUsers.length) {
      setSelectedUserIds(new Set())
    } else {
      setSelectedUserIds(new Set(selectableUsers.map(u => u.id)))
    }
  }

  const handleBulkRoleUpdate = async () => {
    if (selectedUserIds.size === 0) {
      toast.error('No users selected')
      return
    }

    const roleValue = bulkRole === 'none' ? null : bulkRole

    setIsBulkUpdating(true)

    try {
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

      loadUsers()
    } catch (err) {
      setIsBulkUpdating(false)
      toast.error(err instanceof Error ? err.message : 'Failed to update roles')
    }
  }

  const roleOptions = [
    { value: 'none', label: 'No Role (Regular User)', icon: User },
    { value: 'developer', label: 'Developer', icon: Code2 },
    { value: 'admin', label: 'Admin', icon: Shield },
  ]

  const getRoleBadge = (role?: string | null) => {
    if (role === 'admin') {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-red-50 text-red-700 text-[10px] font-mono uppercase tracking-wider border border-red-200">
          <Shield className="h-3 w-3" />
          Admin
        </span>
      )
    }
    if (role === 'developer') {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-50 text-blue-700 text-[10px] font-mono uppercase tracking-wider border border-blue-200">
          <Code2 className="h-3 w-3" />
          Developer
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-zinc-50 text-zinc-600 text-[10px] font-mono uppercase tracking-wider border border-zinc-200">
        <User className="h-3 w-3" />
        User
      </span>
    )
  }

  if (loading) {
    return (
      <BrutalistCard className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
      </BrutalistCard>
    )
  }

  if (error) {
    return (
      <BrutalistCard className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-sm font-mono text-red-600">Error: {error}</p>
          <button
            onClick={loadUsers}
            className="mt-2 px-3 py-1.5 text-xs font-mono border border-zinc-200 hover:border-zinc-900 transition-colors"
          >
            Retry
          </button>
        </div>
      </BrutalistCard>
    )
  }

  if (!data) return null

  const selectableUsers = data.users.filter(
    u => !currentUser || u.clerk_user_id !== currentUser.id
  )
  const allSelected = selectedUserIds.size === selectableUsers.length && selectableUsers.length > 0
  const capacityPercentage = Math.round((data.capacity.used / data.capacity.total) * 100)

  return (
    <div className="space-y-4">
      {/* Capacity Card */}
      <BrutalistCard className="p-4">
        <div className="flex items-center justify-between mb-3">
          <SectionLabel>Platform Capacity</SectionLabel>
          <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center">
            <Users className="h-4 w-4 text-zinc-600" />
          </div>
        </div>
        <div className="space-y-2">
          <p className="text-2xl font-grotesk font-bold tracking-tight">
            {data.capacity.used}
            <span className="text-zinc-400 text-lg">/{data.capacity.total}</span>
          </p>
          <div className="w-full h-2 bg-zinc-100">
            <div
              className={`h-full transition-all ${
                capacityPercentage > 80 ? 'bg-red-500' : capacityPercentage > 60 ? 'bg-amber-500' : 'bg-emerald-500'
              }`}
              style={{ width: `${capacityPercentage}%` }}
            />
          </div>
          <p className="text-xs font-mono text-zinc-500">
            {data.capacity.available} seats available
          </p>
        </div>
      </BrutalistCard>

      {/* Bulk Actions Toolbar */}
      {selectedUserIds.size > 0 && (
        <div className="bg-zinc-900 text-white border-2 border-zinc-900 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-white text-zinc-900 w-8 h-8 flex items-center justify-center">
                <UserCog className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-mono">{selectedUserIds.size} user(s) selected</p>
                <p className="text-[10px] font-mono text-zinc-400">Bulk actions available</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowBulkDialog(true)}
                className="flex items-center gap-2 px-3 py-1.5 bg-white text-zinc-900 text-xs font-mono hover:bg-zinc-100 transition-colors"
              >
                <Edit className="h-3 w-3" />
                Change Roles
              </button>
              <button
                onClick={() => setSelectedUserIds(new Set())}
                className="p-1.5 text-zinc-400 hover:text-white transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Users Table */}
      <BrutalistCard>
        {/* Header */}
        <div className="p-4 border-b border-zinc-200 flex items-center gap-3">
          <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
            <Users className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-grotesk font-bold">All Users</h3>
            <p className="text-[10px] font-mono text-zinc-400">
              Manage platform users and view their activity
            </p>
          </div>
        </div>

        {/* Desktop Table View */}
        <div className="hidden md:block overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50">
                <th className="p-3 w-12">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleSelectAll}
                    className="w-4 h-4 border-2 border-zinc-300 accent-zinc-900"
                    aria-label="Select all users"
                  />
                </th>
                <th className="text-left p-3"><SectionLabel>Email</SectionLabel></th>
                <th className="text-left p-3"><SectionLabel>Role</SectionLabel></th>
                <th className="text-left p-3"><SectionLabel>Status</SectionLabel></th>
                <th className="text-left p-3"><SectionLabel>Joined</SectionLabel></th>
                <th className="text-left p-3"><SectionLabel icon={ListChecks}>Tasks</SectionLabel></th>
                <th className="text-left p-3"><SectionLabel icon={Activity}>Runs</SectionLabel></th>
                <th className="text-left p-3"><SectionLabel icon={Zap}>Triggered</SectionLabel></th>
                <th className="text-left p-3"><SectionLabel>Actions</SectionLabel></th>
              </tr>
            </thead>
            <tbody>
              {data.users.length === 0 ? (
                <tr>
                  <td colSpan={9} className="p-8 text-center">
                    <Users className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
                    <p className="text-xs text-zinc-500 font-mono">No users found</p>
                  </td>
                </tr>
              ) : (
                data.users.map((user) => {
                  const isCurrentUser = currentUser && user.clerk_user_id === currentUser.id
                  return (
                    <tr key={user.id} className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors">
                      <td className="p-3">
                        {!isCurrentUser && (
                          <input
                            type="checkbox"
                            checked={selectedUserIds.has(user.id)}
                            onChange={() => toggleUserSelection(user.id)}
                            className="w-4 h-4 border-2 border-zinc-300 accent-zinc-900"
                            aria-label={`Select ${user.email}`}
                          />
                        )}
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-mono text-zinc-900">{user.email}</span>
                          {isCurrentUser && (
                            <span className="px-1.5 py-0.5 bg-zinc-900 text-white text-[9px] font-mono uppercase tracking-wider">
                              You
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-3">{getRoleBadge(user.role)}</td>
                      <td className="p-3">
                        <StatusBadge variant={user.is_active ? 'active' : 'paused'} />
                      </td>
                      <td className="p-3 text-xs font-mono text-zinc-500">
                        {user.created_at
                          ? formatDistanceToNow(new Date(user.created_at), { addSuffix: true })
                          : '-'}
                      </td>
                      <td className="p-3 text-sm font-mono text-zinc-900">{user.task_count}</td>
                      <td className="p-3 text-sm font-mono text-zinc-900">{user.total_executions}</td>
                      <td className="p-3">
                        <span className="inline-flex items-center gap-1 text-sm font-mono text-emerald-600">
                          <Zap className="h-3 w-3" />
                          {user.conditions_met_count}
                        </span>
                      </td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditRole(user)}
                            disabled={isCurrentUser}
                            className="flex items-center gap-1 px-2 py-1 border border-zinc-200 text-xs font-mono text-zinc-600 hover:border-zinc-900 hover:text-zinc-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <Edit className="h-3 w-3" />
                            Role
                          </button>
                          {user.is_active && !isCurrentUser && (
                            <button
                              onClick={() => handleDeactivate(user.id, user.email)}
                              className="px-2 py-1 border border-red-200 text-xs font-mono text-red-600 hover:border-red-500 hover:bg-red-50 transition-colors"
                            >
                              Deactivate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Mobile Card View */}
        <div className="block md:hidden p-4 space-y-3">
          {data.users.length === 0 ? (
            <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
              <Users className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
              <p className="text-xs text-zinc-500 font-mono">No users found</p>
            </div>
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
      </BrutalistCard>

      {/* Single User Role Edit Dialog */}
      <Dialog open={!!editingUser} onOpenChange={() => setEditingUser(null)}>
        <DialogContent className="border-2 border-zinc-900 p-0">
          <DialogHeader className="p-4 border-b border-zinc-200">
            <DialogTitle className="font-grotesk">Edit User Role</DialogTitle>
            <DialogDescription className="text-xs font-mono text-zinc-500">
              Change the role for {editingUser?.email}
            </DialogDescription>
          </DialogHeader>
          <div className="p-4">
            <div className="relative">
              <button
                onClick={() => setShowRoleDropdown(!showRoleDropdown)}
                className="flex items-center justify-between w-full px-3 py-2 border-2 border-zinc-200 bg-white text-sm font-mono text-zinc-900 hover:border-zinc-400 transition-colors"
              >
                {roleOptions.find(o => o.value === selectedRole)?.label || 'Select a role'}
                <ChevronDown className={`h-4 w-4 text-zinc-400 transition-transform ${showRoleDropdown ? 'rotate-180' : ''}`} />
              </button>
              {showRoleDropdown && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowRoleDropdown(false)} />
                  <div className="absolute left-0 right-0 mt-1 bg-white border-2 border-zinc-900 z-20 shadow-lg">
                    {roleOptions.map((option) => {
                      const Icon = option.icon
                      return (
                        <button
                          key={option.value}
                          onClick={() => {
                            setSelectedRole(option.value)
                            setShowRoleDropdown(false)
                          }}
                          className={`w-full flex items-center gap-2 text-left px-3 py-2 text-sm font-mono hover:bg-zinc-50 transition-colors ${
                            selectedRole === option.value ? 'bg-zinc-900 text-white hover:bg-zinc-900' : ''
                          }`}
                        >
                          <Icon className="h-4 w-4" />
                          {option.label}
                        </button>
                      )
                    })}
                  </div>
                </>
              )}
            </div>
          </div>
          <DialogFooter className="p-4 border-t border-zinc-200 gap-2">
            <button
              onClick={() => setEditingUser(null)}
              disabled={isUpdating}
              className="px-4 py-2 border border-zinc-200 text-zinc-600 text-sm font-mono hover:border-zinc-400 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdateRole}
              disabled={isUpdating}
              className="px-4 py-2 bg-zinc-900 text-white text-sm font-mono hover:bg-[hsl(10,90%,55%)] transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isUpdating && <Loader2 className="h-4 w-4 animate-spin" />}
              {isUpdating ? 'Updating...' : 'Update Role'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Role Edit Dialog */}
      <Dialog open={showBulkDialog} onOpenChange={setShowBulkDialog}>
        <DialogContent className="border-2 border-zinc-900 p-0">
          <DialogHeader className="p-4 border-b border-zinc-200">
            <DialogTitle className="font-grotesk">Bulk Update Roles</DialogTitle>
            <DialogDescription className="text-xs font-mono text-zinc-500">
              Change the role for {selectedUserIds.size} selected user(s)
            </DialogDescription>
          </DialogHeader>
          <div className="p-4 space-y-4">
            <div className="relative">
              <button
                onClick={() => setShowBulkRoleDropdown(!showBulkRoleDropdown)}
                className="flex items-center justify-between w-full px-3 py-2 border-2 border-zinc-200 bg-white text-sm font-mono text-zinc-900 hover:border-zinc-400 transition-colors"
              >
                {roleOptions.find(o => o.value === bulkRole)?.label || 'Select a role'}
                <ChevronDown className={`h-4 w-4 text-zinc-400 transition-transform ${showBulkRoleDropdown ? 'rotate-180' : ''}`} />
              </button>
              {showBulkRoleDropdown && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setShowBulkRoleDropdown(false)} />
                  <div className="absolute left-0 right-0 mt-1 bg-white border-2 border-zinc-900 z-20 shadow-lg">
                    {roleOptions.map((option) => {
                      const Icon = option.icon
                      return (
                        <button
                          key={option.value}
                          onClick={() => {
                            setBulkRole(option.value)
                            setShowBulkRoleDropdown(false)
                          }}
                          className={`w-full flex items-center gap-2 text-left px-3 py-2 text-sm font-mono hover:bg-zinc-50 transition-colors ${
                            bulkRole === option.value ? 'bg-zinc-900 text-white hover:bg-zinc-900' : ''
                          }`}
                        >
                          <Icon className="h-4 w-4" />
                          {option.label}
                        </button>
                      )
                    })}
                  </div>
                </>
              )}
            </div>
            <div className="p-3 bg-zinc-50 border border-zinc-200 max-h-40 overflow-y-auto">
              <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-400 mb-2">Selected users:</p>
              <ul className="space-y-1">
                {data?.users
                  .filter(u => selectedUserIds.has(u.id))
                  .map(u => (
                    <li key={u.id} className="text-xs font-mono text-zinc-600">• {u.email}</li>
                  ))}
              </ul>
            </div>
          </div>
          <DialogFooter className="p-4 border-t border-zinc-200 gap-2">
            <button
              onClick={() => setShowBulkDialog(false)}
              disabled={isBulkUpdating}
              className="px-4 py-2 border border-zinc-200 text-zinc-600 text-sm font-mono hover:border-zinc-400 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleBulkRoleUpdate}
              disabled={isBulkUpdating || !bulkRole}
              className="px-4 py-2 bg-zinc-900 text-white text-sm font-mono hover:bg-[hsl(10,90%,55%)] transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isBulkUpdating && <Loader2 className="h-4 w-4 animate-spin" />}
              {isBulkUpdating ? 'Updating...' : 'Update Roles'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
