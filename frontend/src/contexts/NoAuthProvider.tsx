import React, { ReactNode, useState, useCallback, useMemo } from 'react'
import { AuthContext, AuthContextType, User } from './AuthContext'
import { api } from '@/lib/api'

interface NoAuthProviderProps {
  children: ReactNode
}

// Must match backend NOAUTH_TEST_USER_ID in clerk_auth.py
const NOAUTH_TEST_USER_ID = '00000000-0000-0000-0000-000000000001'

const INITIAL_MOCK_USER: User = {
  id: NOAUTH_TEST_USER_ID,
  email: 'dev@torale.local',
  firstName: 'Dev',
  lastName: 'User',
}

export const NoAuthProvider: React.FC<NoAuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User>(INITIAL_MOCK_USER)

  const syncUser = useCallback(async () => {
    try {
      const backendUser = await api.getCurrentUser()
      setUser({
        id: backendUser.id,
        email: backendUser.email,
        firstName: 'Dev',
        lastName: 'User',
        username: backendUser.username || undefined,
      })
    } catch (error) {
      console.error('Failed to sync user in noauth mode:', error)
    }
  }, [])

  const authValue: AuthContextType = useMemo(
    () => ({
      isLoaded: true,
      isAuthenticated: true,
      user,
      getToken: async () => null, // No token in dev mode
      syncUser,
      signOut: async () => {
        console.log('Sign out called in no-auth mode (no-op)')
      },
    }),
    [syncUser]
  )

  return <AuthContext.Provider value={authValue}>{children}</AuthContext.Provider>
}
