import { useState } from 'react'
import { Navigate, Link } from 'react-router-dom'
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
  { id: 'tasks', label: 'Tasks', icon: Search },
  { id: 'executions', label: 'Executions', icon: Activity },
  { id: 'errors', label: 'Errors', icon: AlertTriangle },
  { id: 'users', label: 'Users', icon: Users },
  { id: 'waitlist', label: 'Waitlist', icon: UserPlus },
]

export function Admin() {
  const { user, isLoaded } = useAuth()
  const [activeTab, setActiveTab] = useState<AdminTab>('overview')

  // Wait for user to load
  if (!isLoaded || !user) {
    return (
      <div className="min-h-screen bg-zinc-50 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
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
    <div className="min-h-screen bg-zinc-50">
      <main className="p-4 md:p-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono mb-2">
            <Link to="/dashboard" className="hover:text-zinc-900 transition-colors">Dashboard</Link>
            <span>/</span>
            <span className="text-zinc-900">Admin</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-zinc-900 text-white w-10 h-10 flex items-center justify-center">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold font-grotesk tracking-tight">Admin Console</h1>
              <p className="text-sm text-zinc-500 font-mono">Platform management and monitoring</p>
            </div>
          </div>
        </header>

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
                      ? 'bg-zinc-900 text-white'
                      : 'bg-white border border-zinc-200 text-zinc-600 hover:border-zinc-400 hover:text-zinc-900'
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
          {activeTab === 'tasks' && <TasksTable />}
          {activeTab === 'executions' && <ExecutionsTable />}
          {activeTab === 'errors' && <ErrorsList />}
          {activeTab === 'users' && <UsersTable />}
          {activeTab === 'waitlist' && <WaitlistTable />}
        </div>
      </main>
    </div>
  )
}
