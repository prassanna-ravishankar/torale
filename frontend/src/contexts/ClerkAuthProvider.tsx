'use client'

import React, { ReactNode, useMemo, useEffect, useCallback, useState } from 'react'
import { useAuth as useClerkAuth, useUser } from '@clerk/nextjs'
import { AuthContext, AuthContextType, AuthUser } from './AuthContext'
import { ApiError, createApiClient, type UserRead } from '@/lib/api'
import { initPostHog, resetPostHog } from '@/lib/posthog'

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

const errorMessage = (error: unknown): string => {
  if (error instanceof ApiError && error.status === 401) {
    return 'Your session could not be verified. Please sign in again.'
  }
  return 'We could not finish loading your account. Please try again.'
}

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
      let userData: UserRead
      try {
        userData = await api.getCurrentUser()
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 404) throw error
        const synced = await api.syncUser()
        userData = synced.user
      }
      setBackendUser(createAuthUser(userData, clerkUser))
      setBootstrapError(null)
    } catch (error) {
      console.error('Failed to load backend user:', error)
      setBackendUser(null)
      setBootstrapError(errorMessage(error))
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

  const resolvedUser = backendUser?.clerkId === userId ? backendUser : null

  const status: AuthContextType['status'] = !clerkIsLoaded
    ? 'loading'
    : !userId
      ? 'unauthenticated'
      : bootstrapError
        ? 'error'
        : resolvedUser
          ? 'authenticated'
          : 'loading'

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
