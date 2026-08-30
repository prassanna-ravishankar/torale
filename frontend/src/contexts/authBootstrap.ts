import type { AuthContextType, AuthUser } from './AuthContext'
import { ApiError, type ApiClient, type UserRead } from '@/lib/api'

type BackendUserApi = Pick<ApiClient, 'getCurrentUser' | 'syncUser'>

export async function fetchBackendUser(api: BackendUserApi): Promise<UserRead> {
  try {
    return await api.getCurrentUser()
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 404) throw error
    return (await api.syncUser()).user
  }
}

export function getAuthErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    return 'Your session could not be verified. Please sign in again.'
  }
  return 'We could not finish loading your account. Please try again.'
}

export function resolveAuthState(
  clerkIsLoaded: boolean,
  userId: string | null | undefined,
  backendUser: AuthUser | null,
  bootstrapError: string | null,
): Pick<AuthContextType, 'status' | 'user'> {
  const user = backendUser?.clerkId === userId ? backendUser : null
  const status: AuthContextType['status'] = !clerkIsLoaded
    ? 'loading'
    : !userId
      ? 'unauthenticated'
      : bootstrapError
        ? 'error'
        : user
          ? 'authenticated'
          : 'loading'
  return { status, user }
}
