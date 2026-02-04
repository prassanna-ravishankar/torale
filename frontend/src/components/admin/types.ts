import type { StatusVariant } from '@/components/torale/StatusBadge'

export interface TaskData {
  id: string
  name: string
  search_query: string
  state: string
  next_run: string | null
  has_notification: boolean
  created_at: string
  user_email: string
  execution_count: number
  trigger_count: number
  last_known_state: string | null
  state_changed_at: string | null
}

export interface UserData {
  id: string
  email: string
  clerk_user_id: string
  is_active: boolean
  created_at: string
  task_count: number
  total_executions: number
  notifications_count: number
  role?: string | null
}

export interface UsersDataResponse {
  users: UserData[]
  capacity: {
    used: number
    total: number
    available: number
  }
}

const VALID_VARIANTS: Set<string> = new Set([
  'active', 'paused', 'completed', 'success', 'failed', 'pending', 'running', 'triggered',
])

export function stateToVariant(state: string): StatusVariant {
  if (VALID_VARIANTS.has(state)) {
    return state as StatusVariant
  }
  return 'unknown'
}
