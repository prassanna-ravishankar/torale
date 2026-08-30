import { describe, expect, it, vi } from 'vitest'

import { ApiError, type ApiClient, type UserRead } from '@/lib/api'
import type { AuthUser } from './AuthContext'
import { fetchBackendUser, getAuthErrorMessage, resolveAuthState } from './authBootstrap'

const backendUser: UserRead = {
  id: 'database-id',
  clerk_user_id: 'clerk-id',
  email: 'user@example.com',
  first_name: null,
  username: null,
  is_active: true,
  has_seen_welcome: false,
  created_at: '2026-01-01T00:00:00Z',
}

const api = (getCurrentUser: () => Promise<UserRead>, syncUser = vi.fn()) => ({
  getCurrentUser,
  syncUser,
}) as unknown as Pick<ApiClient, 'getCurrentUser' | 'syncUser'>

describe('backend auth bootstrap', () => {
  it('uses an existing backend user without syncing', async () => {
    const syncUser = vi.fn()
    await expect(fetchBackendUser(api(vi.fn().mockResolvedValue(backendUser), syncUser)))
      .resolves.toBe(backendUser)
    expect(syncUser).not.toHaveBeenCalled()
  })

  it('syncs only when the backend user is missing', async () => {
    const syncUser = vi.fn().mockResolvedValue({ user: backendUser, created: true })
    await expect(fetchBackendUser(api(
      vi.fn().mockRejectedValue(new ApiError(404, 'User not found')),
      syncUser,
    ))).resolves.toBe(backendUser)
    expect(syncUser).toHaveBeenCalledOnce()
  })

  it('preserves auth failures instead of creating a user', async () => {
    const error = new ApiError(401, 'Expired token')
    const syncUser = vi.fn()
    await expect(fetchBackendUser(api(vi.fn().mockRejectedValue(error), syncUser))).rejects.toBe(error)
    expect(syncUser).not.toHaveBeenCalled()
    expect(getAuthErrorMessage(error)).toBe('Your session could not be verified. Please sign in again.')
  })
})

describe('auth state resolution', () => {
  const user = { clerkId: 'clerk-id' } as AuthUser

  it.each([
    [false, 'clerk-id', user, null, 'loading', user],
    [true, null, user, null, 'unauthenticated', null],
    [true, 'other-account', user, null, 'loading', null],
    [true, 'clerk-id', null, 'Failed', 'error', null],
    [true, 'clerk-id', user, null, 'authenticated', user],
  ] as const)(
    'resolves loaded=%s userId=%s with backend=%s',
    (loaded, userId, backend, error, status, resolvedUser) => {
      expect(resolveAuthState(loaded, userId, backend, error)).toEqual({
        status,
        user: resolvedUser,
      })
    },
  )
})
