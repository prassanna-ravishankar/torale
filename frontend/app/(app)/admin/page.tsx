'use client'

import { AppShell } from '@/components/app/AppShell'
import { Admin } from '@/route-views/Admin'

export default function AdminRoutePage() {
  return (
    <AppShell crumbs={[{ label: 'Admin' }]}>
      <Admin />
    </AppShell>
  )
}
