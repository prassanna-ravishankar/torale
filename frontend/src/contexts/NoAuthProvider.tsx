'use client'

import React, { ReactNode, useState, useCallback, useMemo, useEffect } from 'react'
import { AuthContext, AuthContextType, AuthUser } from './AuthContext'
import { createApiClient } from '@/lib/api'
import { initPostHog } from '@/lib/posthog'

interface NoAuthProviderProps {
  children: ReactNode
}

const NOAUTH_TEST_USER_ID = '00000000-0000-0000-0000-000000000001'
const NOAUTH_CLERK_USER_ID = 'test_user_noauth'

const INITIAL_MOCK_USER: AuthUser = {
  databaseId: NOAUTH_TEST_USER_ID,
  clerkId: NOAUTH_CLERK_USER_ID,
  email: 'dev@torale.local',
  firstName: 'Dev',
  lastName: 'User',
}

export const NoAuthProvider: React.FC<NoAuthProviderProps> = ({ children }) => {
  const api = useMemo(() => createApiClient({ authMode: 'noauth' }), [])
  const [user, setUser] = useState<AuthUser>(INITIAL_MOCK_USER)

  useEffect(() => initPostHog(user.databaseId), [user.databaseId])

  const refreshUser = useCallback(async () => {
    try {
      const backendUser = await api.getCurrentUser()
      setUser({
        databaseId: backendUser.id,
        clerkId: backendUser.clerk_user_id,
        email: backendUser.email,
        firstName: backendUser.first_name || 'Dev',
        lastName: 'User',
        username: backendUser.username,
        has_seen_welcome: backendUser.has_seen_welcome,
      })
    } catch (error) {
      console.error('Failed to refresh user in noauth mode:', error)
    }
  }, [api])

  useEffect(() => {
    void refreshUser()
  }, [refreshUser])

  const authValue: AuthContextType = useMemo(
    () => ({
      status: 'authenticated',
      user,
      api,
      error: null,
      getToken: async () => null,
      refreshUser,
      retryAuth: () => void refreshUser(),
      signOut: async () => undefined,
    }),
    [api, refreshUser, user]
  )

  return <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
}
