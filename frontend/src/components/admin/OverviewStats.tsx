import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Users, ListChecks, Activity, TrendingUp, Loader2, Search, Zap } from 'lucide-react'

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
      <div className="flex items-center justify-center h-64 bg-white border-2 border-zinc-200">
        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-white border-2 border-zinc-200">
        <div className="text-center">
          <p className="text-sm font-mono text-red-600">Error: {error}</p>
          <button
            onClick={loadStats}
            className="mt-2 px-3 py-1.5 text-xs font-mono border border-zinc-200 hover:border-zinc-900 transition-colors"
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
        <div className="bg-white border-2 border-zinc-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
              User Capacity
            </span>
            <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center">
              <Users className="h-4 w-4 text-zinc-600" />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-grotesk font-bold tracking-tight">
              {stats.users.total}
              <span className="text-zinc-400 text-lg">/{stats.users.capacity}</span>
            </p>
            <div className="w-full h-2 bg-zinc-100">
              <div
                className={`h-full transition-all ${
                  capacityPercentage > 80 ? 'bg-red-500' : capacityPercentage > 60 ? 'bg-amber-500' : 'bg-emerald-500'
                }`}
                style={{ width: `${capacityPercentage}%` }}
              />
            </div>
            <p className="text-xs font-mono text-zinc-500">
              {stats.users.available} seats available
            </p>
          </div>
        </div>

        {/* Active Tasks */}
        <div className="bg-white border-2 border-zinc-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
              Active Tasks
            </span>
            <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center">
              <ListChecks className="h-4 w-4 text-zinc-600" />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-grotesk font-bold tracking-tight">
              {stats.tasks.total}
            </p>
            <div className="flex items-center gap-2">
              <Zap className="h-3 w-3 text-emerald-600" />
              <span className="text-xs font-mono text-zinc-600">
                {stats.tasks.triggered} triggered
              </span>
              <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-mono border border-emerald-200">
                {stats.tasks.trigger_rate}
              </span>
            </div>
          </div>
        </div>

        {/* 24h Executions */}
        <div className="bg-white border-2 border-zinc-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
              24h Executions
            </span>
            <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center">
              <Activity className="h-4 w-4 text-zinc-600" />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-grotesk font-bold tracking-tight">
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
        </div>

        {/* Success Rate */}
        <div className="bg-white border-2 border-zinc-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
              Success Rate
            </span>
            <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center">
              <TrendingUp className="h-4 w-4 text-zinc-600" />
            </div>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-grotesk font-bold tracking-tight text-emerald-600">
              {stats.executions_24h.success_rate}
            </p>
            <p className="text-xs font-mono text-zinc-500">Last 24 hours</p>
          </div>
        </div>
      </div>

      {/* Popular Queries */}
      <div className="bg-white border-2 border-zinc-200">
        <div className="p-4 border-b border-zinc-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-grotesk font-bold">Popular Queries</h3>
            <p className="text-[10px] font-mono text-zinc-400 mt-0.5">
              Top 10 most common search queries
            </p>
          </div>
          <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center">
            <Search className="h-4 w-4" />
          </div>
        </div>
        <div className="p-4">
          {stats.popular_queries.length === 0 ? (
            <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
              <Search className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
              <p className="text-xs text-zinc-500 font-mono">No queries yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {stats.popular_queries.map((query, index) => (
                <div
                  key={index}
                  className="flex items-center gap-3 p-3 border border-zinc-200 hover:border-zinc-300 transition-colors"
                >
                  <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center shrink-0 text-xs font-mono font-bold text-zinc-500">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-mono text-zinc-900 truncate">
                      {query.search_query}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-mono text-zinc-500">
                        {query.count} {query.count === 1 ? 'task' : 'tasks'}
                      </span>
                      <span className="text-zinc-300">|</span>
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
      </div>
    </div>
  )
}
