// @vitest-environment jsdom

import React from 'react'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthContext, type AuthContextType } from '@/contexts/AuthContext'
import { createApiClient } from '@/lib/api'
import { AuthReadyBoundary } from './AuthReadyBoundary'

const navigation = vi.hoisted(() => ({
  replace: vi.fn(),
  push: vi.fn(),
  pathname: '/dashboard/tasks/watch/id',
  search: 'tab=history&filter=sent',
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: navigation.replace, push: navigation.push }),
  usePathname: () => navigation.pathname,
  useSearchParams: () => new URLSearchParams(navigation.search),
}))

const value = (
  status: AuthContextType['status'],
  overrides: Partial<AuthContextType> = {},
): AuthContextType => ({
  status,
  user: status === 'authenticated' ? {
    databaseId: 'database-id',
    clerkId: 'clerk-id',
    email: 'user@example.com',
  } : null,
  api: createApiClient({ authMode: 'noauth' }),
  error: status === 'error' ? 'Account bootstrap failed' : null,
  getToken: async () => null,
  retryAuth: vi.fn(),
  ...overrides,
})

const renderBoundary = (context: AuthContextType) => render(
  <AuthContext.Provider value={context}>
    <AuthReadyBoundary><div>private watch</div></AuthReadyBoundary>
  </AuthContext.Provider>,
)

describe('AuthReadyBoundary', () => {
  beforeEach(() => {
    navigation.replace.mockReset()
    navigation.push.mockReset()
  })

  afterEach(cleanup)

  it('keeps route children unmounted while backend auth is loading', () => {
    renderBoundary(value('loading'))

    expect(screen.queryByText('private watch')).toBeNull()
    expect(screen.getByText('Loading your watches…')).toBeTruthy()
  })

  it('mounts route children only after authentication completes', () => {
    renderBoundary(value('authenticated'))

    expect(screen.getByText('private watch')).toBeTruthy()
  })

  it('redirects signed-out users and preserves the complete return URL', async () => {
    renderBoundary(value('unauthenticated'))

    await waitFor(() => expect(navigation.replace).toHaveBeenCalledWith(
      '/sign-in?redirect_url=%2Fdashboard%2Ftasks%2Fwatch%2Fid%3Ftab%3Dhistory%26filter%3Dsent',
    ))
    expect(screen.queryByText('private watch')).toBeNull()
    expect(screen.getByText('Taking you to sign in…')).toBeTruthy()
  })

  it('exposes working retry and sign-out actions for bootstrap errors', async () => {
    const retryAuth = vi.fn()
    const signOut = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderBoundary(value('error', { retryAuth, signOut }))

    expect(screen.getByRole('heading', { name: 'We couldn’t load your account' })).toBeTruthy()
    expect(screen.getByText('Account bootstrap failed')).toBeTruthy()
    expect(screen.queryByText('private watch')).toBeNull()

    await user.click(screen.getByRole('button', { name: 'Try again' }))
    await user.click(screen.getByRole('button', { name: 'Sign out' }))

    expect(retryAuth).toHaveBeenCalledOnce()
    expect(signOut).toHaveBeenCalledOnce()
  })
})
