'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { AppShell } from '@/components/app/AppShell'
import { ConnectorsPage } from '@/route-views/ConnectorsPage'
import { useAuth } from '@/contexts/AuthContext'
import { connectorsEnabled } from '@/components/connectors/connectorsFlag'

export default function ConnectorsRoutePage() {
  const { user } = useAuth()
  const router = useRouter()
  const allowed = connectorsEnabled(user)

  useEffect(() => {
    if (allowed === false) {
      router.replace('/settings/notifications')
    }
  }, [allowed, router])

  if (!allowed) return null

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
