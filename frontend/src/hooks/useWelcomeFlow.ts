import { api } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'

export function useWelcomeFlow() {
  const { refreshUser } = useAuth()

  const handleWelcomeComplete = async () => {
    try {
      await api.markWelcomeSeen()
      if (refreshUser) {
        await refreshUser()
      }
    } catch (error) {
      console.error('Failed to mark welcome as seen:', error)
      // Still proceed - don't trap user
    }
  }

  return { handleWelcomeComplete }
}
