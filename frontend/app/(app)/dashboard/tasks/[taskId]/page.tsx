'use client'

import { useRouter, useParams } from 'next/navigation'
import { TaskDetail } from '@/components/TaskDetail'
import { useAuth } from '@/contexts/AuthContext'

// Owner-view watch detail. Lives in (app) where Clerk is already mounted;
// authenticated user reads via the API client owned by AuthProvider. Anonymous
// /tasks/[taskId] in the (marketing) tree handles the public read path —
// the two routes are intentionally distinct (see review notif-bbeb3471 /
// B1) so the public route stays SSG without auth dependency.
export default function OwnerTaskDetailPage() {
  const router = useRouter()
  const params = useParams<{ taskId: string }>()
  const { user } = useAuth()

  const taskId = params?.taskId
  if (!taskId) {
    router.replace('/dashboard')
    return null
  }

  // AuthReadyBoundary guarantees the backend user exists before this route
  // mounts. This guard only protects the type boundary during transitions.
  if (!user) return null

  return (
    <TaskDetail
      taskId={taskId}
      onBack={() => router.push('/dashboard')}
      onDeleted={() => router.push('/dashboard')}
      currentUserId={user.databaseId}
    />
  )
}
