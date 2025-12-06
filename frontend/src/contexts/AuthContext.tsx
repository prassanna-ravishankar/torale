import React, { createContext, useContext, ReactNode } from 'react'
import { ClerkAuthProvider } from './ClerkAuthProvider'
import { NoAuthProvider } from './NoAuthProvider'

export interface User {
  id: string
  email: string
  username?: string | null
  firstName?: string
  lastName?: string
  imageUrl?: string
  publicMetadata?: {
    role?: string
    [key: string]: any
  }
}

export interface AuthContextType {
  // Core auth state
  isLoaded: boolean
  isAuthenticated: boolean
  user: User | null

  // Token management
  getToken: () => Promise<string | null>

  // User sync (only needed for Clerk mode)
  syncUser?: () => Promise<void>

  // Auth actions (only available in Clerk mode)
  signOut?: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const noAuth = import.meta.env.VITE_TORALE_NOAUTH === '1'

  if (noAuth) {
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
