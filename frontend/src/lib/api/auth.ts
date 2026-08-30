import type { ApiKey, CreateApiKeyResponse } from '@/types'
import type { ApiTransport } from './transport'

export interface UserRead {
  id: string
  clerk_user_id: string
  email: string
  first_name: string | null
  username: string | null
  is_active: boolean
  has_seen_welcome: boolean
  created_at: string
}

export interface SyncUserResponse { user: UserRead; created: boolean }

export const createAuthApi = (transport: ApiTransport) => ({
  syncUser: () => transport.request<SyncUserResponse>('/auth/sync-user', { method: 'POST' }),
  getCurrentUser: () => transport.request<UserRead>('/auth/me'),
  markWelcomeSeen: () => transport.request<void>('/auth/mark-welcome-seen', { method: 'POST' }),
  createApiKey: (name: string) => transport.request<CreateApiKeyResponse>('/auth/api-keys', {
    method: 'POST', body: JSON.stringify({ name }),
  }),
  getApiKeys: () => transport.request<ApiKey[]>('/auth/api-keys'),
  revokeApiKey: (keyId: string) => transport.request<{ status: string }>(`/auth/api-keys/${keyId}`, {
    method: 'DELETE',
  }),
})

export type AuthApi = ReturnType<typeof createAuthApi>
