'use client'

import { useRouter } from 'next/navigation'
import { FirstTimeExperience } from './FirstTimeExperience'
import { useWelcomeFlow } from '@/hooks/useWelcomeFlow'

export function Welcome() {
  const router = useRouter()
  const { handleWelcomeComplete } = useWelcomeFlow()

  const handleComplete = async () => {
    await handleWelcomeComplete()
    router.push('/dashboard')
  }

  return <FirstTimeExperience onComplete={handleComplete} />
}
