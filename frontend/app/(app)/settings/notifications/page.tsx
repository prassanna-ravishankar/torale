'use client'

import { AppShell } from '@/components/app/AppShell'
import { NotificationSettingsPage } from '@/route-views/NotificationSettingsPage'

export default function NotificationsSettingsRoutePage() {
  return (
    <AppShell
      crumbs={[
        { label: 'Settings', href: '/settings' },
        { label: 'Notifications' },
      ]}
    >
      <NotificationSettingsPage />
    </AppShell>
  )
}
