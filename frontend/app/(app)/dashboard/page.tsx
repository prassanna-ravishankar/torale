'use client'

import { useRouter } from 'next/navigation'
import { ownerWatchPath } from '@/lib/watchRoutes'
import { Dashboard } from '@/components/Dashboard'

export default function DashboardPage() {
  const router = useRouter()
  const handleTaskClick = (taskId: string, justCreated?: boolean) => {
    router.push(
      `${ownerWatchPath(taskId)}${justCreated ? '?justCreated=true' : ''}`,
    )
  }
  return <Dashboard onTaskClick={handleTaskClick} />
}
