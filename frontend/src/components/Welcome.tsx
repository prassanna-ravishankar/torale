import { useNavigate } from 'react-router-dom'
import { FirstTimeExperience } from './FirstTimeExperience'
import { api } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'

export function Welcome() {
  const navigate = useNavigate()
  const { refreshUser } = useAuth()

  const handleComplete = async () => {
    try {
      await api.markWelcomeSeen()
      if (refreshUser) {
        await refreshUser()
      }
    } catch (error) {
      console.error('Failed to mark welcome as seen:', error)
      // Still navigate - don't trap user
    } finally {
      navigate('/dashboard')
    }
  }

  return <FirstTimeExperience onComplete={handleComplete} />
}
