'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { AppShell } from '@/components/app/AppShell'
import { ConnectorsPage } from '@/route-views/ConnectorsPage'
import { useAuth } from '@/contexts/AuthContext'
import { connectorsEnabled } from '@/components/connectors/connectorsFlag'

export default function ConnectorsRoutePage() {
  const { isLoaded, user } = useAuth()
  const router = useRouter()
  const allowed = isLoaded ? connectorsEnabled(user) : null

  useEffect(() => {
    if (allowed === false) {
      router.replace('/settings/notifications')
    }
  }, [allowed, router])

  if (!isLoaded || allowed === false) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <AppShell
      crumbs={[
        { label: 'Settings', href: '/settings' },
        { label: 'Connectors' },
      ]}
    >
      <ConnectorsPage />
    </AppShell>
  )
}
