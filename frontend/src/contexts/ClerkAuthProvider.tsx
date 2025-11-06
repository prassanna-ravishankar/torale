import React, { ReactNode, useMemo } from 'react'
import { ClerkProvider, useAuth as useClerkAuth, useUser } from '@clerk/clerk-react'
import { AuthContext, AuthContextType, User } from './AuthContext'

const CLERK_PUBLISHABLE_KEY = window.CONFIG?.clerkPublishableKey || import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

interface ClerkAuthProviderProps {
  children: ReactNode
}

const ClerkAuthWrapper: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isLoaded: clerkIsLoaded, userId, getToken: clerkGetToken, signOut } = useClerkAuth()
  const { user: clerkUser } = useUser()

  const user: User | null = useMemo(() => {
    if (!clerkUser) return null
    return {
      id: clerkUser.id,
      email: clerkUser.primaryEmailAddress?.emailAddress || '',
      firstName: clerkUser.firstName || undefined,
      lastName: clerkUser.lastName || undefined,
      imageUrl: clerkUser.imageUrl,
    }
  }, [clerkUser])

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
      signOut: async () => {
        await signOut()
      },
    }),
    [clerkIsLoaded, userId, user, clerkGetToken, signOut]
  )

  return <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
}

export const ClerkAuthProvider: React.FC<ClerkAuthProviderProps> = ({ children }) => {
  if (!CLERK_PUBLISHABLE_KEY) {
    throw new Error('Missing Clerk Publishable Key. Set VITE_CLERK_PUBLISHABLE_KEY or enable no-auth mode with VITE_TORALE_NOAUTH=1')
  }

  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <ClerkAuthWrapper>{children}</ClerkAuthWrapper>
    </ClerkProvider>
  )
}
