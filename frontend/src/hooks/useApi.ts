import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { api } from '@/lib/api'

/**
 * Hook to initialize the API client with Clerk authentication.
 * Call this once at the app level to set up the token getter.
 */
export function useApiSetup() {
  const { getToken } = useAuth()

  useEffect(() => {
    // Set the token getter for the API client
    api.setTokenGetter(() => getToken())
  }, [getToken])
}

/**
 * Hook that provides the configured API client.
 * The app must call useApiSetup() first.
 */
export function useApi() {
  return api
}
