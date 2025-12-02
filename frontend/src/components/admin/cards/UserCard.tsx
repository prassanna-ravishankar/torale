import { formatDistanceToNow } from 'date-fns'
import { Edit, User, CheckCircle2, XCircle, Shield, Code } from 'lucide-react'

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

interface UserCardProps {
  user: UserData
  currentUserClerkId?: string
  onDeactivate: (userId: string, email: string) => void
  onEditRole: (user: UserData) => void
}

export function UserCard({ user, currentUserClerkId, onDeactivate, onEditRole }: UserCardProps) {
  const getRoleBadge = (role?: string | null) => {
    if (role === 'admin') {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-red-50 text-red-700 text-[9px] font-mono uppercase tracking-wider border border-red-200">
          <Shield className="h-3 w-3" />
          Admin
        </span>
      )
    }
    if (role === 'developer') {
      return (
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-50 text-blue-700 text-[9px] font-mono uppercase tracking-wider border border-blue-200">
          <Code className="h-3 w-3" />
          Developer
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-zinc-50 text-zinc-600 text-[9px] font-mono uppercase tracking-wider border border-zinc-200">
        <User className="h-3 w-3" />
        User
      </span>
    )
  }

  const isCurrentUser = currentUserClerkId && user.clerk_user_id === currentUserClerkId

  return (
    <div className="p-3 border border-zinc-200 hover:border-zinc-300 transition-colors">
      <div className="space-y-3">
        <div className="flex items-start gap-3">
          <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center shrink-0">
            <User className="h-4 w-4 text-zinc-600" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-xs font-mono text-zinc-900 break-all" title={user.email}>{user.email}</p>
                <p className="text-[10px] font-mono text-zinc-400 mt-0.5">
                  Joined {user.created_at
                    ? formatDistanceToNow(new Date(user.created_at), { addSuffix: true })
                    : '-'}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              {user.is_active ? (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[9px] font-mono uppercase tracking-wider border border-emerald-200">
                  <CheckCircle2 className="h-3 w-3" />
                  Active
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-zinc-100 text-zinc-500 text-[9px] font-mono uppercase tracking-wider border border-zinc-200">
                  <XCircle className="h-3 w-3" />
                  Inactive
                </span>
              )}
              {getRoleBadge(user.role)}
              {isCurrentUser && (
                <span className="px-1.5 py-0.5 bg-zinc-900 text-white text-[9px] font-mono uppercase tracking-wider">
                  You
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
          <div className="p-2 bg-zinc-50 border border-zinc-200 text-center">
            <p className="text-zinc-400 uppercase tracking-wider">Tasks</p>
            <p className="text-zinc-900 font-bold text-sm mt-0.5">{user.task_count}</p>
          </div>
          <div className="p-2 bg-zinc-50 border border-zinc-200 text-center">
            <p className="text-zinc-400 uppercase tracking-wider">Runs</p>
            <p className="text-zinc-900 font-bold text-sm mt-0.5">{user.total_executions}</p>
          </div>
          <div className="p-2 bg-zinc-50 border border-zinc-200 text-center">
            <p className="text-zinc-400 uppercase tracking-wider">Triggers</p>
            <p className="text-zinc-900 font-bold text-sm mt-0.5">{user.conditions_met_count}</p>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => onEditRole(user)}
            disabled={isCurrentUser}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 border border-zinc-200 text-zinc-600 hover:border-zinc-400 hover:text-zinc-900 transition-colors text-xs font-mono disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Edit className="h-3 w-3" />
            Edit Role
          </button>
          {user.is_active && (
            <button
              onClick={() => onDeactivate(user.id, user.email)}
              className="flex-1 px-3 py-2 bg-red-600 text-white hover:bg-red-700 transition-colors text-xs font-mono"
            >
              Deactivate
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
