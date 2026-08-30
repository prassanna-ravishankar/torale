import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'

import { AuthContext, type AuthContextType } from '@/contexts/AuthContext'
import { createApiClient } from '@/lib/api'
import { AuthReadyBoundary } from './AuthReadyBoundary'

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => '/dashboard',
  useSearchParams: () => new URLSearchParams(),
}))

const renderBoundary = (status: AuthContextType['status'], error: string | null = null) =>
  renderToStaticMarkup(
    <AuthContext.Provider value={{
      status,
      user: null,
      api: createApiClient({ authMode: 'noauth' }),
      error,
      getToken: async () => null,
      retryAuth: vi.fn(),
    }}>
      <AuthReadyBoundary><div>private watch</div></AuthReadyBoundary>
    </AuthContext.Provider>,
  )

describe('AuthReadyBoundary', () => {
  it('mounts private content only after authentication', () => {
    expect(renderBoundary('loading')).not.toContain('private watch')
    expect(renderBoundary('authenticated')).toContain('private watch')
  })

  it('renders a recoverable bootstrap error without private content', () => {
    const html = renderBoundary('error', 'Account bootstrap failed')
    expect(html).toContain('Account bootstrap failed')
    expect(html).toContain('Try again')
    expect(html).not.toContain('private watch')
  })
})
