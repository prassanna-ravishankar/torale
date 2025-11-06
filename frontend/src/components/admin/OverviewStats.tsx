import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { Users, ListChecks, Activity, TrendingUp } from 'lucide-react'

interface PlatformStats {
  users: {
    total: number
    capacity: number
    available: number
  }
  tasks: {
    total: number
    triggered: number
    trigger_rate: string
  }
  executions_24h: {
    total: number
    failed: number
    success_rate: string
  }
  popular_queries: Array<{
    search_query: string
    count: number
    triggered_count: number
  }>
}

export function OverviewStats() {
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      setLoading(true)
      const data = await api.getAdminStats()
      setStats(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading stats...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-destructive">Error: {error}</div>
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">User Capacity</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.users.total}/{stats.users.capacity}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats.users.available} seats available
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
            <ListChecks className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.tasks.total}</div>
            <p className="text-xs text-muted-foreground">
              {stats.tasks.triggered} triggered ({stats.tasks.trigger_rate})
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">24h Executions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.executions_24h.total}</div>
            <p className="text-xs text-muted-foreground">
              {stats.executions_24h.failed} failed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.executions_24h.success_rate}</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Popular Queries</CardTitle>
          <CardDescription>Top 10 most common search queries</CardDescription>
        </CardHeader>
        <CardContent>
          {stats.popular_queries.length === 0 ? (
            <p className="text-sm text-muted-foreground">No queries yet</p>
          ) : (
            <div className="space-y-3">
              {stats.popular_queries.map((query, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium truncate">{query.search_query}</p>
                    <p className="text-xs text-muted-foreground">
                      {query.count} tasks • {query.triggered_count} triggered
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
