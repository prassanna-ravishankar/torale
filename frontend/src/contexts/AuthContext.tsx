'use client'

import React, { createContext, useContext, ReactNode } from 'react'
import { NoAuthProvider } from './NoAuthProvider'
import { ClerkAuthProvider } from './ClerkAuthProvider'

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

/**
 * AuthProvider mounts inside the (app) and (auth) route groups only. The
 * route-group split is the structural replacement for the runtime
 * `__client_uat`-cookie probe used in the Vite era — marketing routes never
 * see this provider (their tree never mounts ClerkProvider either), so the
 * previous PendingAuthProvider / MarketingAuthProvider / lazy-Clerk branches
 * are gone.
 *
 * NEXT_PUBLIC_WEBWHEN_NOAUTH=1 is the local-dev escape hatch — the layout
 * around this provider switches off the same env var to skip <ClerkProvider>
 * entirely, and this provider returns a stable mock user.
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  if (process.env.NEXT_PUBLIC_WEBWHEN_NOAUTH === '1') {
    return <NoAuthProvider>{children}</NoAuthProvider>
  }
  return <ClerkAuthProvider>{children}</ClerkAuthProvider>
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export { AuthContext }
