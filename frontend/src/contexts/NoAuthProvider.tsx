import React, { ReactNode, useMemo } from 'react'
import { AuthContext, AuthContextType, User } from './AuthContext'

interface NoAuthProviderProps {
  children: ReactNode
}

// Must match backend NOAUTH_TEST_USER_ID in clerk_auth.py
const NOAUTH_TEST_USER_ID = '00000000-0000-0000-0000-000000000001'

const MOCK_USER: User = {
  id: NOAUTH_TEST_USER_ID,
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
