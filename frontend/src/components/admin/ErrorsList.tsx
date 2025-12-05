import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { AlertTriangle, Loader2, CheckCircle2, Search, User, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { SectionLabel, BrutalistCard } from '@/components/torale'

interface ErrorExecution {
  id: string
  task_id: string
  started_at: string
  completed_at: string | null
  error_message: string | null
  search_query: string
  task_name: string
  user_email: string
}

export function ErrorsList() {
  const [errors, setErrors] = useState<ErrorExecution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadErrors()
  }, [])

  const loadErrors = async () => {
    try {
      setLoading(true)
      const data = await api.getAdminErrors({ limit: 50 })
      setErrors(data.errors)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load errors')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <BrutalistCard className="flex items-center justify-center h-64">
        <Loader2 className="h-6 w-6 animate-spin text-zinc-400" />
      </BrutalistCard>
    )
  }

  if (error) {
    return (
      <BrutalistCard className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-sm font-mono text-red-600">Error: {error}</p>
          <button
            onClick={loadErrors}
            className="mt-2 px-3 py-1.5 text-xs font-mono border border-zinc-200 hover:border-zinc-900 transition-colors"
          >
            Retry
          </button>
        </div>
      </BrutalistCard>
    )
  }

  return (
    <BrutalistCard>
      {/* Header */}
      <div className="p-4 border-b border-zinc-200 flex items-center gap-3">
        <div className="bg-red-600 text-white w-8 h-8 flex items-center justify-center shrink-0">
          <AlertTriangle className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-sm font-grotesk font-bold">Recent Errors</h3>
          <p className="text-[10px] font-mono text-zinc-400">
            Failed task executions requiring attention
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {errors.length === 0 ? (
          <div className="p-8 bg-emerald-50 border-2 border-emerald-200 text-center">
            <CheckCircle2 className="h-8 w-8 text-emerald-600 mx-auto mb-3" />
            <p className="text-sm font-grotesk font-bold text-emerald-900">System Healthy</p>
            <p className="text-xs font-mono text-emerald-700 mt-1">No recent errors detected</p>
          </div>
        ) : (
          <div className="space-y-4">
            {errors.map((errorExec) => (
              <div key={errorExec.id} className="border-2 border-red-200 bg-red-50">
                {/* Error Header */}
                <div className="p-3 border-b border-red-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <AlertTriangle className="h-4 w-4 text-red-600 flex-shrink-0" />
                    <span className="text-sm font-mono text-red-900 truncate">
                      {errorExec.task_name}
                    </span>
                  </div>
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono text-red-600">
                    <Clock className="h-3 w-3" />
                    {errorExec.started_at
                      ? formatDistanceToNow(new Date(errorExec.started_at), { addSuffix: true })
                      : 'Unknown'}
                  </span>
                </div>

                {/* Error Body */}
                <div className="p-3 space-y-3">
                  {/* User */}
                  <div className="flex items-center gap-2">
                    <User className="h-3 w-3 text-red-400 flex-shrink-0" />
                    <span className="text-xs font-mono text-red-700">{errorExec.user_email}</span>
                  </div>

                  {/* Query */}
                  <div>
                    <div className="mb-1">
                      <SectionLabel icon={Search} className="text-red-500">Query</SectionLabel>
                    </div>
                    <p className="text-xs font-mono text-red-800 break-words pl-4">
                      {errorExec.search_query}
                    </p>
                  </div>

                  {/* Error Message */}
                  <div>
                    <div className="mb-1">
                      <SectionLabel icon={AlertTriangle} className="text-red-500">Error</SectionLabel>
                    </div>
                    <div className="p-2 bg-red-100 border border-red-300 ml-4">
                      <p className="text-xs font-mono text-red-900 break-words">
                        {errorExec.error_message || 'No error message available'}
                      </p>
                    </div>
                  </div>

                  {/* Task ID */}
                  <div className="pt-2 border-t border-red-200">
                    <p className="text-[10px] font-mono text-red-400 truncate" title={errorExec.task_id}>
                      Task ID: {errorExec.task_id}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </BrutalistCard>
  )
}
