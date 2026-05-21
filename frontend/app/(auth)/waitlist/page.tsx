'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { CapacityGate } from '@/components/CapacityGate'
import { WaitlistPage } from '@/components/WaitlistPage'

function SignUpRedirect() {
  const router = useRouter()
  useEffect(() => {
    router.replace('/sign-up')
  }, [router])
  return null
}

export default function WaitlistRoutePage() {
  return (
    <CapacityGate fallback={<WaitlistPage />}>
      <SignUpRedirect />
    </CapacityGate>
  )
}
