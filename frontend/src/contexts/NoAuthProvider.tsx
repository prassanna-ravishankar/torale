import React, { ReactNode, useMemo } from 'react'
import { AuthContext, AuthContextType, User } from './AuthContext'

interface NoAuthProviderProps {
  children: ReactNode
}

const MOCK_USER: User = {
  id: 'dev-user-id',
  email: 'dev@torale.local',
  firstName: 'Dev',
  lastName: 'User',
}

export const NoAuthProvider: React.FC<NoAuthProviderProps> = ({ children }) => {
  const authValue: AuthContextType = useMemo(
    () => ({
      isLoaded: true,
      isAuthenticated: true,
      user: MOCK_USER,
      getToken: async () => null, // No token in dev mode
      signOut: async () => {
        console.log('Sign out called in no-auth mode (no-op)')
      },
    }),
    []
  )

  return <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
}
