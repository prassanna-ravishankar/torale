import { Navigate } from 'react-router-dom'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { OverviewStats } from '@/components/admin/OverviewStats'
import { QueriesTable } from '@/components/admin/QueriesTable'
import { ExecutionsTable } from '@/components/admin/ExecutionsTable'
import { TemporalMonitor } from '@/components/admin/TemporalMonitor'
import { ErrorsList } from '@/components/admin/ErrorsList'
import { UsersTable } from '@/components/admin/UsersTable'
import { Shield } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export function Admin() {
  const { user, isLoaded } = useAuth()

  // Wait for user to load
  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Loading...</div>
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
    <div className="container mx-auto py-8 space-y-6">
      <div className="flex items-center gap-3">
        <Shield className="h-8 w-8" />
        <div>
          <h1 className="text-3xl font-bold">Admin Console</h1>
          <p className="text-muted-foreground">Platform management and monitoring</p>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="queries">Queries</TabsTrigger>
          <TabsTrigger value="executions">Executions</TabsTrigger>
          <TabsTrigger value="temporal">Temporal</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewStats />
        </TabsContent>

        <TabsContent value="queries">
          <QueriesTable />
        </TabsContent>

        <TabsContent value="executions">
          <ExecutionsTable />
        </TabsContent>

        <TabsContent value="temporal">
          <TemporalMonitor />
        </TabsContent>

        <TabsContent value="errors">
          <ErrorsList />
        </TabsContent>

        <TabsContent value="users">
          <UsersTable />
        </TabsContent>
      </Tabs>
    </div>
  )
}
