// @vitest-environment jsdom

import React from 'react'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, type SyncUserResponse, type UserRead } from '@/lib/api'
import { useAuth } from './AuthContext'
import { ClerkAuthProvider } from './ClerkAuthProvider'

const mocks = vi.hoisted(() => ({
  clerk: {
    isLoaded: true,
    userId: 'clerk-a' as string | null,
    user: {
      firstName: 'Clerk',
      lastName: 'User',
      imageUrl: 'https://example.com/avatar.png',
      publicMetadata: {},
    } as Record<string, unknown> | null,
  },
  getToken: vi.fn().mockResolvedValue('token'),
  signOut: vi.fn().mockResolvedValue(undefined),
  getCurrentUser: vi.fn<() => Promise<UserRead>>(),
  syncUser: vi.fn<() => Promise<SyncUserResponse>>(),
  initPostHog: vi.fn(),
  resetPostHog: vi.fn(),
}))

vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({
    isLoaded: mocks.clerk.isLoaded,
    userId: mocks.clerk.userId,
    getToken: mocks.getToken,
    signOut: mocks.signOut,
  }),
  useUser: () => ({ user: mocks.clerk.user }),
}))

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...actual,
    createApiClient: () => ({
      getCurrentUser: mocks.getCurrentUser,
      syncUser: mocks.syncUser,
    }),
  }
})

vi.mock('@/lib/posthog', () => ({
  initPostHog: mocks.initPostHog,
  resetPostHog: mocks.resetPostHog,
}))

const backendUser = (overrides: Partial<UserRead> = {}): UserRead => ({
  id: 'database-a',
  clerk_user_id: 'clerk-a',
  email: 'a@example.com',
  first_name: 'Backend',
  username: 'watcher-a',
  is_active: true,
  has_seen_welcome: true,
  created_at: '2026-01-01T00:00:00Z',
  ...overrides,
})

function AuthProbe() {
  const { status, user, error } = useAuth()
  return <output>{JSON.stringify({ status, user, error })}</output>
}

const readAuth = () => JSON.parse(screen.getByRole('status').textContent || '{}') as {
  status: string
  user: { databaseId: string; clerkId: string; email: string } | null
  error: string | null
}

describe('ClerkAuthProvider', () => {
  beforeEach(() => {
    mocks.clerk.isLoaded = true
    mocks.clerk.userId = 'clerk-a'
    mocks.clerk.user = {
      firstName: 'Clerk',
      lastName: 'User',
      imageUrl: 'https://example.com/avatar.png',
      publicMetadata: {},
    }
    mocks.getToken.mockClear()
    mocks.signOut.mockClear()
    mocks.getCurrentUser.mockReset()
    mocks.syncUser.mockReset()
    mocks.initPostHog.mockClear()
    mocks.resetPostHog.mockClear()
    vi.spyOn(console, 'error').mockImplementation(() => undefined)
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('authenticates with an existing backend user without syncing', async () => {
    mocks.getCurrentUser.mockResolvedValue(backendUser())
    render(<ClerkAuthProvider><AuthProbe /></ClerkAuthProvider>)

    await waitFor(() => expect(readAuth().status).toBe('authenticated'))
    expect(readAuth().user).toMatchObject({
      databaseId: 'database-a', clerkId: 'clerk-a', email: 'a@example.com',
    })
    expect(mocks.syncUser).not.toHaveBeenCalled()
    expect(mocks.initPostHog).toHaveBeenCalledWith('database-a')
  })

  it('syncs a first-time user only when the backend lookup returns 404', async () => {
    const synced = backendUser({ id: 'database-new', email: 'new@example.com' })
    mocks.getCurrentUser.mockRejectedValue(new ApiError(404, 'User not found'))
    mocks.syncUser.mockResolvedValue({ user: synced, created: true })
    render(<ClerkAuthProvider><AuthProbe /></ClerkAuthProvider>)

    await waitFor(() => expect(readAuth().status).toBe('authenticated'))
    expect(mocks.getCurrentUser).toHaveBeenCalledOnce()
    expect(mocks.syncUser).toHaveBeenCalledOnce()
    expect(readAuth().user?.databaseId).toBe('database-new')
  })

  it('surfaces verification errors without attempting user creation', async () => {
    mocks.getCurrentUser.mockRejectedValue(new ApiError(401, 'Expired token'))
    render(<ClerkAuthProvider><AuthProbe /></ClerkAuthProvider>)

    await waitFor(() => expect(readAuth().status).toBe('error'))
    expect(readAuth()).toMatchObject({
      user: null,
      error: 'Your session could not be verified. Please sign in again.',
    })
    expect(mocks.syncUser).not.toHaveBeenCalled()
  })

  it('clears the backend account when Clerk signs out', async () => {
    mocks.getCurrentUser.mockResolvedValue(backendUser())
    const view = render(<ClerkAuthProvider><AuthProbe /></ClerkAuthProvider>)
    await waitFor(() => expect(readAuth().status).toBe('authenticated'))

    mocks.clerk.userId = null
    mocks.clerk.user = null
    view.rerender(<ClerkAuthProvider><AuthProbe /></ClerkAuthProvider>)

    await waitFor(() => expect(readAuth().status).toBe('unauthenticated'))
    expect(readAuth().user).toBeNull()
    expect(mocks.resetPostHog).toHaveBeenCalled()
  })

  it('does not expose the previous backend account while Clerk changes users', async () => {
    mocks.getCurrentUser
      .mockResolvedValueOnce(backendUser())
      .mockResolvedValueOnce(backendUser({
        id: 'database-b',
        clerk_user_id: 'clerk-b',
        email: 'b@example.com',
      }))
    const view = render(<ClerkAuthProvider><AuthProbe /></ClerkAuthProvider>)
    await waitFor(() => expect(readAuth().status).toBe('authenticated'))

    mocks.clerk.userId = 'clerk-b'
    mocks.clerk.user = {
      firstName: 'Second',
      lastName: 'User',
      imageUrl: 'https://example.com/second.png',
      publicMetadata: {},
    }
    view.rerender(<ClerkAuthProvider><AuthProbe /></ClerkAuthProvider>)

    expect(readAuth()).toMatchObject({ status: 'loading', user: null })
    await waitFor(() => expect(readAuth().status).toBe('authenticated'))
    expect(readAuth().user).toMatchObject({
      databaseId: 'database-b', clerkId: 'clerk-b', email: 'b@example.com',
    })
    expect(mocks.getCurrentUser).toHaveBeenCalledTimes(2)
  })
})
