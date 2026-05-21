'use client'

import { AppShell } from '@/components/app/AppShell'
import { Welcome } from '@/components/Welcome'

export default function WelcomeRoutePage() {
  return (
    <AppShell crumbs={[{ label: 'Welcome' }]}>
      <Welcome />
    </AppShell>
  )
}
