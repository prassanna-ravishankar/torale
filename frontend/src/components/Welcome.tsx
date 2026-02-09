import { useNavigate } from 'react-router-dom'
import { FirstTimeExperience } from './FirstTimeExperience'
import { useWelcomeFlow } from '@/hooks/useWelcomeFlow'

export function Welcome() {
  const navigate = useNavigate()
  const { handleWelcomeComplete } = useWelcomeFlow()

  const handleComplete = async () => {
    await handleWelcomeComplete()
    navigate('/dashboard')
  }

  return <FirstTimeExperience onComplete={handleComplete} />
}
