import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

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
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading errors...</div>
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

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg sm:text-xl">Recent Errors</CardTitle>
        <CardDescription className="text-sm">Failed task executions requiring attention</CardDescription>
      </CardHeader>
      <CardContent>
        {errors.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            No recent errors - system is healthy!
          </p>
        ) : (
          <div className="space-y-4">
            {errors.map((errorExec) => (
              <Alert key={errorExec.id} variant="destructive">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <AlertTitle className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-2">
                  <span className="min-w-0 truncate text-sm sm:text-base">
                    {errorExec.task_name} - {errorExec.user_email}
                  </span>
                  <span className="text-xs font-normal flex-shrink-0">
                    {errorExec.started_at
                      ? formatDistanceToNow(new Date(errorExec.started_at), { addSuffix: true })
                      : 'Unknown'}
                  </span>
                </AlertTitle>
                <AlertDescription>
                  <div className="space-y-2 mt-2">
                    <div>
                      <p className="text-xs font-semibold">Query:</p>
                      <p className="text-xs break-words">{errorExec.search_query}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold">Error:</p>
                      <p className="text-xs font-mono break-words">
                        {errorExec.error_message || 'No error message available'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground font-mono truncate" title={errorExec.task_id}>
                        Task ID: {errorExec.task_id}
                      </p>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
