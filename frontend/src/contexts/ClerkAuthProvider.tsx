'use client'

import React, { ReactNode, useMemo, useEffect, useCallback, useState } from 'react'
import { useAuth as useClerkAuth, useUser } from '@clerk/nextjs'
import { AuthContext, AuthContextType, AuthUser } from './AuthContext'
import { createApiClient, type UserRead } from '@/lib/api'
import { initPostHog, resetPostHog } from '@/lib/posthog'
import { fetchBackendUser, getAuthErrorMessage, resolveAuthState } from './authBootstrap'

interface ClerkAuthProviderProps {
  children: ReactNode
}

const createAuthUser = (
  backendUser: UserRead,
  clerkUser: {
    firstName?: string | null
    lastName?: string | null
    imageUrl?: string
    publicMetadata?: Record<string, unknown>
  }
): AuthUser => ({
  databaseId: backendUser.id,
  clerkId: backendUser.clerk_user_id,
  email: backendUser.email,
  username: backendUser.username,
  has_seen_welcome: backendUser.has_seen_welcome,
  firstName: clerkUser.firstName || backendUser.first_name || undefined,
  lastName: clerkUser.lastName || undefined,
  imageUrl: clerkUser.imageUrl,
  publicMetadata: clerkUser.publicMetadata as AuthUser['publicMetadata'],
})

export const ClerkAuthProvider: React.FC<ClerkAuthProviderProps> = ({ children }) => {
  const { isLoaded: clerkIsLoaded, userId, getToken: clerkGetToken, signOut } = useClerkAuth()
  const { user: clerkUser } = useUser()
  const [backendUser, setBackendUser] = useState<AuthUser | null>(null)
  const [bootstrapError, setBootstrapError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  const getToken = useCallback(
    async (options?: { skipCache?: boolean }) => clerkGetToken(options),
    [clerkGetToken]
  )
  const api = useMemo(() => createApiClient({ authMode: 'clerk', getToken }), [getToken])

  const loadBackendUser = useCallback(async () => {
    if (!clerkUser) return
    try {
      const userData = await fetchBackendUser(api)
      setBackendUser(createAuthUser(userData, clerkUser))
      setBootstrapError(null)
    } catch (error) {
      console.error('Failed to load backend user:', error)
      setBackendUser(null)
      setBootstrapError(getAuthErrorMessage(error))
    }
  }, [api, clerkUser])

  useEffect(() => {
    if (!clerkIsLoaded || !userId || !clerkUser) {
      setBackendUser(null)
      setBootstrapError(null)
      return
    }
    void loadBackendUser()
  }, [attempt, clerkIsLoaded, clerkUser, loadBackendUser, userId])

  useEffect(() => {
    if (backendUser) initPostHog(backendUser.databaseId)
    else if (clerkIsLoaded && !userId) resetPostHog()
  }, [backendUser, clerkIsLoaded, userId])

  const refreshUser = useCallback(async () => {
    await loadBackendUser()
  }, [loadBackendUser])

  const retryAuth = useCallback(() => {
    setBootstrapError(null)
    setAttempt(value => value + 1)
  }, [])

  const { status, user: resolvedUser } = resolveAuthState(
    clerkIsLoaded, userId, backendUser, bootstrapError,
  )

  const authValue: AuthContextType = useMemo(
    () => ({
      status,
      user: resolvedUser,
      api,
      error: bootstrapError,
      getToken: () => getToken(),
      refreshUser,
      retryAuth,
      signOut,
    }),
    [api, bootstrapError, getToken, refreshUser, resolvedUser, retryAuth, signOut, status]
  )

  return <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
}
