import { useState, useCallback } from 'react'
import { Navigate } from 'react-router-dom'
import { OverviewStats } from '@/components/admin/OverviewStats'
import { TasksTable } from '@/components/admin/TasksTable'
import { ExecutionsTable } from '@/components/admin/ExecutionsTable'
import { ErrorsList } from '@/components/admin/ErrorsList'
import { UsersTable } from '@/components/admin/UsersTable'
import { WaitlistTable } from '@/components/admin/WaitlistTable'
import { Shield, BarChart3, Search, Activity, AlertTriangle, Users, UserPlus, Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

type AdminTab = 'overview' | 'tasks' | 'executions' | 'errors' | 'users' | 'waitlist'

const tabs: { id: AdminTab; label: string; icon: typeof Shield }[] = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'tasks', label: 'Watches', icon: Search },
  { id: 'executions', label: 'Executions', icon: Activity },
  { id: 'errors', label: 'Errors', icon: AlertTriangle },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'waitlist', label: 'Waitlist', icon: UserPlus },
]

export function Admin() {
  const { user, isLoaded } = useAuth()
  const [activeTab, setActiveTab] = useState<AdminTab>('overview')
  const [taskIdToExpand, setTaskIdToExpand] = useState<string | null>(null)

  const handleExecutionClick = useCallback((taskId: string) => {
    setTaskIdToExpand(taskId)
    setActiveTab('tasks')
  }, [])

  // Wait for user to load
  if (!isLoaded || !user) {
    return (
      <div className="min-h-screen bg-ink-8 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-ink-4" />
      </div>
    )
  }

  // Check if user is admin
  const isAdmin = user?.publicMetadata?.role === 'admin'

  // Redirect non-admins to dashboard
  if (!isAdmin) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="min-h-screen bg-ink-8">
      <main className="p-4 md:p-8">
        {/* Tab Navigation */}
        <div className="mb-6 overflow-x-auto">
          <div className="flex gap-1 min-w-max pb-2">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 text-xs font-mono transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'bg-ink-1 text-white'
                      : 'bg-white border border-ink-6 text-ink-3 hover:border-ink-4 hover:text-ink-0'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'overview' && <OverviewStats />}
          {activeTab === 'tasks' && <TasksTable initialExpandedTaskId={taskIdToExpand} />}
          {activeTab === 'executions' && (
            <ExecutionsTable onTaskClick={handleExecutionClick} />
          )}
          {activeTab === 'errors' && <ErrorsList />}
          {activeTab === 'users' && <UsersTable />}
          {activeTab === 'waitlist' && <WaitlistTable />}
        </div>
      </main>
    </div>
  )
}
