'use client'

import { useRouter, useParams } from 'next/navigation'
import { TaskDetail } from '@/components/TaskDetail'
import { useAuth } from '@/contexts/AuthContext'

// Owner-view watch detail. Lives in (app) where Clerk is already mounted;
// authed user reads via the existing useApiSetup axios client. Anonymous
// /tasks/[taskId] in the (marketing) tree handles the public read path —
// the two routes are intentionally distinct (see review notif-bbeb3471 /
// B1) so the public route stays SSG without auth dependency.
export default function OwnerTaskDetailPage() {
  const router = useRouter()
  const params = useParams<{ taskId: string }>()
  const { isLoaded, user } = useAuth()

  const taskId = params?.taskId
  if (!taskId) {
    router.replace('/dashboard')
    return null
  }

  // A cold deep-link (for example, from a notification email) can render this
  // page before AuthedApiBootstrap's effect has installed the Clerk token
  // getter. Waiting for the backend user mirrors Dashboard's loading gate and
  // prevents the initial anonymous 404 from becoming a permanent not-found
  // state. Navigating from the dashboard already has this user ready.
  if (!isLoaded || !user?.id) return null

  return (
    <TaskDetail
      taskId={taskId}
      onBack={() => router.push('/dashboard')}
      onDeleted={() => router.push('/dashboard')}
      currentUserId={user.id}
    />
  )
}
