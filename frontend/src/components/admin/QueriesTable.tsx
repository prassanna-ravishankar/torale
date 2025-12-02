import { useCallback, useEffect, useState } from 'react'
import { Switch } from '@/components/ui/switch'
import { api } from '@/lib/api'
import { QueryCard } from './cards/QueryCard'
import { CronDisplay } from '@/components/ui/CronDisplay'
import { Loader2, Search, Zap, CheckCircle2, XCircle } from 'lucide-react'

interface Query {
  id: string
  name: string
  search_query: string
  condition_description: string
  schedule: string
  is_active: boolean
  condition_met: boolean
  created_at: string
  user_email: string
  execution_count: number
  trigger_count: number
}

export function QueriesTable() {
  const [queries, setQueries] = useState<Query[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeOnly, setActiveOnly] = useState(false)

  const loadQueries = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.getAdminQueries({ limit: 100, active_only: activeOnly })
      setQueries(data.queries)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load queries')
    } finally {
      setLoading(false)
    }
  }, [activeOnly])

  useEffect(() => {
    loadQueries()
  }, [loadQueries])

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
            onClick={loadQueries}
            className="mt-2 px-3 py-1.5 text-xs font-mono border border-zinc-200 hover:border-zinc-900 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border-2 border-zinc-200">
      {/* Header */}
      <div className="p-4 border-b border-zinc-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
            <Search className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-grotesk font-bold">All User Queries</h3>
            <p className="text-[10px] font-mono text-zinc-400">
              Monitor all search queries and conditions across users
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Switch
            id="active-only"
            checked={activeOnly}
            onCheckedChange={setActiveOnly}
            className="data-[state=checked]:bg-zinc-900 data-[state=unchecked]:bg-zinc-200 border-2 border-zinc-900"
          />
          <label htmlFor="active-only" className="text-xs font-mono text-zinc-600 whitespace-nowrap">
            Active only
          </label>
        </div>
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-200 bg-zinc-50">
              <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">User</th>
              <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Name</th>
              <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Search Query</th>
              <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Condition</th>
              <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Schedule</th>
              <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Status</th>
              <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Executions</th>
              <th className="text-left p-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500">Triggered</th>
            </tr>
          </thead>
          <tbody>
            {queries.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center">
                  <Search className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
                  <p className="text-xs text-zinc-500 font-mono">No queries found</p>
                </td>
              </tr>
            ) : (
              queries.map((query) => (
                <tr key={query.id} className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors">
                  <td className="p-3 text-xs font-mono text-zinc-600">{query.user_email}</td>
                  <td className="p-3 text-sm font-mono text-zinc-900">{query.name}</td>
                  <td className="p-3 text-xs font-mono text-zinc-700 max-w-xs truncate">{query.search_query}</td>
                  <td className="p-3 text-xs text-zinc-500 max-w-xs truncate">{query.condition_description}</td>
                  <td className="p-3 text-xs">
                    <CronDisplay cron={query.schedule} showRaw={false} className="text-xs font-mono" />
                  </td>
                  <td className="p-3">
                    <div className="flex gap-1">
                      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono uppercase tracking-wider border ${
                        query.is_active
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-zinc-50 text-zinc-500 border-zinc-200'
                      }`}>
                        {query.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {query.condition_met && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-mono uppercase tracking-wider border border-emerald-200">
                          <Zap className="h-3 w-3" />
                          Met
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="p-3 text-sm font-mono text-zinc-900">{query.execution_count}</td>
                  <td className="p-3">
                    <span className="inline-flex items-center gap-1 text-sm font-mono text-emerald-600">
                      <Zap className="h-3 w-3" />
                      {query.trigger_count}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="block md:hidden p-4 space-y-3">
        {queries.length === 0 ? (
          <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
            <Search className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
            <p className="text-xs text-zinc-500 font-mono">No queries found</p>
          </div>
        ) : (
          queries.map((query) => <QueryCard key={query.id} query={query} />)
        )}
      </div>
    </div>
  )
}
