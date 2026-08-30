import { useCallback, useEffect, useState } from 'react'
import { getErrorMessage } from '@/lib/utils'
import { useApi } from '@/hooks/useApi';
import { Users, ListChecks, Activity, TrendingUp, Loader2, Search, Zap } from 'lucide-react'
import { SectionLabel, Card } from '@/components/torale'

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
  const api = useApi()
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadStats = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getAdminStats<PlatformStats>()
      setStats(data)
      setError(null)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load stats'))
    } finally {
      setLoading(false)
    }
  }, [api])

  useEffect(() => {
    void loadStats()
  }, [loadStats])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 bg-white border border-ink-6">
        <Loader2 className="h-6 w-6 animate-spin text-ink-4" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-white border border-ink-6">
        <div className="text-center">
          <p className="text-sm font-mono text-red-600">Error: {error}</p>
          <button
            onClick={loadStats}
            className="mt-2 px-3 py-1.5 text-xs font-mono border border-ink-6 hover:border-ink-2 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!stats) return null

  // Calculate capacity percentage for visual indicator
  const capacityPercentage = Math.round((stats.users.total / stats.users.capacity) * 100)

  return (
    <div className="space-y-6">
      {/* KPI Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* User Capacity */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <SectionLabel>User Capacity</SectionLabel>
            <div className="bg-ink-7 w-8 h-8 flex items-center justify-center">
              <Users className="h-4 w-4 text-ink-3" />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-bold tracking-tight">
              {stats.users.total}
              <span className="text-ink-4 text-lg">/{stats.users.capacity}</span>
            </p>
            <div className="w-full h-2 bg-ink-7">
              <div
                className={`h-full transition-all ${
                  capacityPercentage > 80 ? 'bg-red-500' : capacityPercentage > 60 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${Math.min(capacityPercentage, 100)}%` }}
              />
            </div>
            <p className="text-xs font-mono text-ink-3">
              {stats.users.available} seats available
            </p>
          </div>
        </Card>

        {/* Active Tasks */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <SectionLabel>Active Watches</SectionLabel>
            <div className="bg-ink-7 w-8 h-8 flex items-center justify-center">
              <ListChecks className="h-4 w-4 text-ink-3" />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-bold tracking-tight">
              {stats.tasks.total}
            </p>
            <div className="flex items-center gap-2">
              <Zap className="h-3 w-3 text-emerald-600" />
              <span className="text-xs font-mono text-ink-3">
                {stats.tasks.triggered} triggered
              </span>
              <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-mono border border-emerald-200">
                {stats.tasks.trigger_rate}
              </span>
            </div>
          </div>
        </Card>

        {/* 24h Executions */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <SectionLabel>24h Executions</SectionLabel>
            <div className="bg-ink-7 w-8 h-8 flex items-center justify-center">
              <Activity className="h-4 w-4 text-ink-3" />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-bold tracking-tight">
              {stats.executions_24h.total}
            </p>
            <div className="flex items-center gap-2">
              {stats.executions_24h.failed > 0 ? (
                <span className="px-1.5 py-0.5 bg-red-50 text-red-700 text-[10px] font-mono border border-red-200">
                  {stats.executions_24h.failed} failed
                </span>
              ) : (
                <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-mono border border-emerald-200">
                  0 failed
                </span>
              )}
            </div>
          </div>
        </Card>

        {/* Success Rate */}
        <Card className="p-4">
          <div className="flex items-center justify-between mb-3">
            <SectionLabel>Success Rate</SectionLabel>
            <div className="bg-ink-7 w-8 h-8 flex items-center justify-center">
              <TrendingUp className="h-4 w-4 text-ink-3" />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-bold tracking-tight text-emerald-600">
              {stats.executions_24h.success_rate}
            </p>
            <p className="text-xs font-mono text-ink-3">Last 24 hours</p>
          </div>
        </Card>
      </div>

      {/* Popular Queries */}
      <Card>
        <div className="p-4 border-b border-ink-6 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium">Popular Queries</h3>
            <p className="text-[10px] font-mono text-ink-4 mt-0.5">
              Top 10 most common search queries
            </p>
          </div>
          <div className="bg-ink-1 text-white w-8 h-8 flex items-center justify-center">
            <Search className="h-4 w-4" />
          </div>
        </div>
        <div className="p-4">
          {stats.popular_queries.length === 0 ? (
            <div className="p-4 bg-ink-8 border border-dashed border-ink-5 text-center">
              <Search className="h-5 w-5 text-ink-4 mx-auto mb-2" />
              <p className="text-xs text-ink-3 font-mono">No queries yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {stats.popular_queries.map((query, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 p-3 border border-ink-6 hover:border-ink-5 transition-colors"
                >
                  <div className="bg-ink-7 w-8 h-8 flex items-center justify-center shrink-0 text-xs font-mono font-medium text-ink-3">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-mono text-ink-0 truncate">
                      {query.search_query}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-mono text-ink-3">
                        {query.count} {query.count === 1 ? 'watch' : 'watches'}
                      </span>
                      <span className="text-ink-5">|</span>
                      <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-600">
                        <Zap className="h-3 w-3" />
                        {query.triggered_count} triggered
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}
