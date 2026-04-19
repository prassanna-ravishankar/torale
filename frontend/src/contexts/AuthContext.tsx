import React, { createContext, useContext, ReactNode, Suspense, lazy, useMemo } from 'react'
import { NoAuthProvider } from './NoAuthProvider'

// Lazy-loaded so the Clerk SDK (77 KiB gzip) is not part of the initial bundle.
// Unauthenticated visits to the landing page never need it.
const ClerkAuthProvider = lazy(() =>
  import('./ClerkAuthProvider').then((m) => ({ default: m.ClerkAuthProvider }))
)

export interface User {
  id: string | null // Nullable to handle cases where backend UUID is unavailable
  email: string
  username?: string | null
  firstName?: string
  lastName?: string
  imageUrl?: string
  has_seen_welcome?: boolean
  publicMetadata?: {
    role?: string
    [key: string]: unknown
  }
}

export interface AuthContextType {
  // Core auth state
  isLoaded: boolean
  isAuthenticated: boolean
  user: User | null

  // Token management
  getToken: () => Promise<string | null>

  // Refresh user data (only needed for Clerk mode, after mutations like username change)
  refreshUser?: () => Promise<void>

  // Auth actions (only available in Clerk mode)
  signOut?: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

// Placeholder context while the Clerk SDK chunk is still loading. Mirrors
// Clerk's "not yet loaded" state so consumers (ProtectedRoute, AuthRedirect)
// show their usual spinners instead of redirecting.
const PendingAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const value = useMemo<AuthContextType>(
    () => ({
      isLoaded: false,
      isAuthenticated: false,
      user: null,
      getToken: async () => null,
    }),
    []
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const noAuth = import.meta.env.VITE_TORALE_NOAUTH === '1' || window.__PRERENDER__

  if (noAuth) {
    return <NoAuthProvider>{children}</NoAuthProvider>
  }

  return (
    <Suspense fallback={<PendingAuthProvider>{children}</PendingAuthProvider>}>
      <ClerkAuthProvider>{children}</ClerkAuthProvider>
    </Suspense>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export { AuthContext }
