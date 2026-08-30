'use client'

import React, { createContext, useContext, ReactNode } from 'react'
import { NoAuthProvider } from './NoAuthProvider'
import { ClerkAuthProvider } from './ClerkAuthProvider'
import type { ApiClient } from '@/lib/api'

export interface AuthUser {
  databaseId: string
  clerkId: string
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
  status: 'loading' | 'authenticated' | 'unauthenticated' | 'error'
  user: AuthUser | null
  api: ApiClient
  error: string | null

  // Token management
  getToken: () => Promise<string | null>

  // Refresh user data (only needed for Clerk mode, after mutations like username change)
  refreshUser?: () => Promise<void>
  retryAuth: () => void

  // Auth actions (only available in Clerk mode)
  signOut?: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

/**
 * AuthProvider mounts inside the authenticated (app) route group only. The
 * route-group split is the structural replacement for the runtime
 * `__client_uat`-cookie probe used in the Vite era — marketing routes never
 * auth and marketing trees do not need backend-user state, so the
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
