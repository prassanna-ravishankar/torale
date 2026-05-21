'use client'

import { SignUp } from '@clerk/nextjs'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { CapacityGate } from '@/components/CapacityGate'

function WaitlistRedirect() {
  const router = useRouter()
  useEffect(() => {
    router.replace('/waitlist')
  }, [router])
  return null
}

export default function SignUpRoutePage() {
  return (
    <CapacityGate fallback={<WaitlistRedirect />}>
      <SignUp
        routing="path"
        path="/sign-up"
        signInUrl="/sign-in"
        forceRedirectUrl="/dashboard"
        fallbackRedirectUrl="/dashboard"
      />
    </CapacityGate>
  )
}
