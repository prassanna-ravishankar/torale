import React, { ReactNode, useMemo, useEffect, useState } from 'react'
import { ClerkProvider, useAuth as useClerkAuth, useUser } from '@clerk/clerk-react'
import { AuthContext, AuthContextType, User } from './AuthContext'

const CLERK_PUBLISHABLE_KEY = window.CONFIG?.clerkPublishableKey || import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

interface ClerkAuthProviderProps {
  children: ReactNode
}

/**
 * Helper function to construct a User object from backend data and Clerk user.
 * Reduces duplication between initial fetch, fallback, and sync operations.
 */
const createUserFromData = (
  backendData: { id: string | null; email: string; username: string | null },
  clerkUser: any
): User => ({
  id: backendData.id,
  email: backendData.email,
  username: backendData.username,
  firstName: clerkUser.firstName || undefined,
  lastName: clerkUser.lastName || undefined,
  imageUrl: clerkUser.imageUrl,
  publicMetadata: clerkUser.publicMetadata as { role?: string; [key: string]: any } | undefined,
})

const ClerkAuthWrapper: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isLoaded: clerkIsLoaded, userId, getToken: clerkGetToken, signOut } = useClerkAuth()
  const { user: clerkUser } = useUser()
  const [backendUser, setBackendUser] = useState<User | null>(null)
  const [isFetchingUser, setIsFetchingUser] = useState(false)

  // Fetch user data from backend when Clerk user is available
  useEffect(() => {
    if (!clerkUser || isFetchingUser) return

    const fetchBackendUser = async () => {
      setIsFetchingUser(true)
      try {
        const { api } = await import('@/lib/api')
        const userData = await api.getCurrentUser()
        setBackendUser(createUserFromData(userData, clerkUser))
      } catch (error) {
        console.error('Failed to fetch user from backend:', error)
        // Fallback to Clerk user data without database UUID
        // Set id to null to ensure ownership checks fail safely
        setBackendUser(createUserFromData({
          id: null,
          email: clerkUser.primaryEmailAddress?.emailAddress || '',
          username: null,
        }, clerkUser))
      } finally {
        setIsFetchingUser(false)
      }
    }

    fetchBackendUser()
  }, [clerkUser, isFetchingUser])

  const user: User | null = backendUser

  const authValue: AuthContextType = useMemo(
    () => ({
      isLoaded: clerkIsLoaded,
      isAuthenticated: !!userId,
      user,
      getToken: async () => {
        try {
          return await clerkGetToken()
        } catch (error) {
          console.error('Failed to get Clerk token:', error)
          return null
        }
      },
      syncUser: async () => {
        // Import api client lazily to avoid circular dependency
        const { api } = await import('@/lib/api')
        await api.syncUser()

        // Refresh user data from backend after sync
        if (clerkUser) {
          const userData = await api.getCurrentUser()
          setBackendUser(createUserFromData(userData, clerkUser))
        }
      },
      signOut: async () => {
        await signOut()
      },
    }),
    [clerkIsLoaded, userId, user, clerkGetToken, signOut, clerkUser]
  )

  return <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
}

export const ClerkAuthProvider: React.FC<ClerkAuthProviderProps> = ({ children }) => {
  if (!CLERK_PUBLISHABLE_KEY) {
    throw new Error('Missing Clerk Publishable Key. Set VITE_CLERK_PUBLISHABLE_KEY in your environment.')
  }

  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} waitlistUrl="/waitlist">
      <ClerkAuthWrapper>{children}</ClerkAuthWrapper>
    </ClerkProvider>
  )
}
