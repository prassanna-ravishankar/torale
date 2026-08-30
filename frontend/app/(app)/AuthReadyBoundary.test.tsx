import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthContext, type AuthContextType } from '@/contexts/AuthContext'
import { createApiClient } from '@/lib/api'
import { AuthReadyBoundary } from './AuthReadyBoundary'

const replace = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace, push: vi.fn() }),
  usePathname: () => '/dashboard/tasks/watch-id',
  useSearchParams: () => new URLSearchParams(),
}))

const value = (status: AuthContextType['status']): AuthContextType => ({
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
})

describe('AuthReadyBoundary', () => {
  beforeEach(() => replace.mockClear())

  it('keeps route children unmounted while backend auth is loading', () => {
    const html = renderToStaticMarkup(React.createElement(
      AuthContext.Provider,
      { value: value('loading') },
      React.createElement(AuthReadyBoundary, null, React.createElement('div', null, 'private watch')),
    ))

    expect(html).not.toContain('private watch')
    expect(html).toContain('Loading your watches…')
  })

  it('mounts route children only after authentication completes', () => {
    const html = renderToStaticMarkup(React.createElement(
      AuthContext.Provider,
      { value: value('authenticated') },
      React.createElement(AuthReadyBoundary, null, React.createElement('div', null, 'private watch')),
    ))

    expect(html).toContain('private watch')
  })
})
