'use client'

import React, { ReactNode, useMemo, useEffect, useCallback, useState } from 'react'
import { useAuth as useClerkAuth, useUser } from '@clerk/nextjs'
import { AuthContext, AuthContextType, User } from './AuthContext'
import { initPostHog, resetPostHog } from '@/lib/posthog'

interface ClerkAuthProviderProps {
  children: ReactNode
}

/**
 * Helper to construct a User object from backend data and Clerk user.
 */
const createUserFromData = (
  backendData: { id: string | null; email: string; username: string | null; has_seen_welcome?: boolean },
  clerkUser: { firstName?: string | null; lastName?: string | null; imageUrl?: string; publicMetadata?: Record<string, unknown> }
): User => ({
  id: backendData.id,
  email: backendData.email,
  username: backendData.username,
  has_seen_welcome: backendData.has_seen_welcome,
  firstName: clerkUser.firstName || undefined,
  lastName: clerkUser.lastName || undefined,
  imageUrl: clerkUser.imageUrl,
  publicMetadata: clerkUser.publicMetadata as { role?: string;[key: string]: unknown } | undefined,
})

/**
 * Reads Clerk state via @clerk/nextjs hooks and exposes the AuthContext shape
 * to existing consumers. <ClerkProvider> itself is mounted by the
 * (app)/(auth) route-group layout — this wrapper is only the state bridge.
 */
export const ClerkAuthProvider: React.FC<ClerkAuthProviderProps> = ({ children }) => {
  const { isLoaded: clerkIsLoaded, userId, getToken: clerkGetToken, signOut } = useClerkAuth()
  const { user: clerkUser } = useUser()
  const [backendUser, setBackendUser] = useState<User | null>(null)
  const isFetchingRef = React.useRef(false)

  useEffect(() => {
    if (!clerkUser || isFetchingRef.current) return

    const fetchBackendUser = async () => {
      isFetchingRef.current = true
      try {
        const { api } = await import('@/lib/api')
        const userData = await api.getCurrentUser()
        setBackendUser(createUserFromData(userData, clerkUser))
      } catch (error) {
        console.warn('User not found in backend, syncing automatically...', error)
        try {
          const { api } = await import('@/lib/api')
          await api.syncUser()
          const userData = await api.getCurrentUser()
          setBackendUser(createUserFromData(userData, clerkUser))
        } catch (syncError) {
          console.error('Failed to sync user:', syncError)
          setBackendUser(createUserFromData({
            id: null,
            email: clerkUser.primaryEmailAddress?.emailAddress || '',
            username: null,
          }, clerkUser))
        }
      } finally {
        isFetchingRef.current = false
      }
    }

    fetchBackendUser()
  }, [clerkUser])

  const user: User | null = backendUser

  useEffect(() => {
    if (user?.id) {
      initPostHog(user.id)
    } else if (!user) {
      resetPostHog()
    }
  }, [user])

  const getToken = useCallback(async () => {
    try {
      return await clerkGetToken()
    } catch (error) {
      console.error('Failed to get Clerk token:', error)
      return null
    }
  }, [clerkGetToken])

  const refreshUser = useCallback(async () => {
    if (!clerkUser) return
    const { api } = await import('@/lib/api')
    const userData = await api.getCurrentUser()
    setBackendUser(createUserFromData(userData, clerkUser))
  }, [clerkUser])

  const handleSignOut = useCallback(async () => {
    await signOut()
  }, [signOut])

  const authValue: AuthContextType = useMemo(
    () => ({
      isLoaded: clerkIsLoaded,
      isAuthenticated: !!userId,
      user,
      getToken,
      refreshUser,
      signOut: handleSignOut,
    }),
    [clerkIsLoaded, userId, user, getToken, refreshUser, handleSignOut]
  )

  return <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
}
