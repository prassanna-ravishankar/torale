import { useCallback, useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { formatDistanceToNow } from 'date-fns'
import { formatDuration } from '@/lib/utils'

interface GroundingSource {
  title: string
  uri: string
}

interface Execution {
  id: string
  task_id: string
  status: string
  started_at: string
  completed_at: string | null
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  result: any
  error_message: string | null
  condition_met: boolean | null
  change_summary: string | null
  grounding_sources: GroundingSource[]
  search_query: string
  user_email: string
}

export function ExecutionsTable() {
  const [executions, setExecutions] = useState<Execution[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const loadExecutions = useCallback(async () => {
    try {
      setLoading(true)
      const params: { limit: number; status?: string } = { limit: 50 }
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      const data = await api.getAdminExecutions(params)
      setExecutions(data.executions)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load executions')
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    loadExecutions()
  }, [loadExecutions])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading executions...</div>
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
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0">
          <div className="min-w-0">
            <CardTitle className="text-lg sm:text-xl">Execution History</CardTitle>
            <CardDescription className="text-sm">View all task executions across users</CardDescription>
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-full sm:w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="running">Running</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        {/* Desktop Table View */}
        <div className="hidden md:block">
          <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Query</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Condition</TableHead>
              <TableHead>Started</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Sources</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {executions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground">
                  No executions found
                </TableCell>
              </TableRow>
            ) : (
              executions.map((execution) => (
                <TableRow key={execution.id}>
                  <TableCell className="font-mono text-xs">{execution.user_email}</TableCell>
                  <TableCell className="max-w-xs truncate">{execution.search_query}</TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        execution.status === 'success'
                          ? 'default'
                          : execution.status === 'failed'
                            ? 'destructive'
                            : 'secondary'
                      }
                    >
                      {execution.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {execution.condition_met !== null && (
                      <Badge variant={execution.condition_met ? 'default' : 'outline'}>
                        {execution.condition_met ? 'Met' : 'Not met'}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-xs">
                    {execution.started_at
                      ? formatDistanceToNow(new Date(execution.started_at), { addSuffix: true })
                      : '-'}
                  </TableCell>
                  <TableCell className="text-xs">
                    {formatDuration(execution.started_at, execution.completed_at, '-')}
                  </TableCell>
                  <TableCell className="text-xs">
                    {execution.grounding_sources?.length || 0} sources
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        </div>

        {/* Mobile Card View */}
        <div className="block md:hidden space-y-4">
          {executions.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-8">No executions found</p>
          ) : (
            executions.map((execution) => (
              <Card key={execution.id} className="p-4">
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium break-words">{execution.search_query}</p>
                      <p className="text-xs text-muted-foreground font-mono truncate mt-0.5">{execution.user_email}</p>
                    </div>
                    <Badge
                      variant={
                        execution.status === 'success'
                          ? 'default'
                          : execution.status === 'failed'
                            ? 'destructive'
                            : 'secondary'
                      }
                      className="text-xs flex-shrink-0"
                    >
                      {execution.status}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {execution.condition_met !== null && (
                      <div>
                        <span className="text-xs text-muted-foreground">Condition: </span>
                        <Badge variant={execution.condition_met ? 'default' : 'outline'} className="text-xs">
                          {execution.condition_met ? 'Met' : 'Not met'}
                        </Badge>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <div>
                      <span className="font-medium">Started:</span>{' '}
                      {execution.started_at
                        ? formatDistanceToNow(new Date(execution.started_at), { addSuffix: true })
                        : '-'}
                    </div>
                    <div>
                      <span className="font-medium">Duration:</span>{' '}
                      {formatDuration(execution.started_at, execution.completed_at, '-')}
                    </div>
                    <div>
                      <span className="font-medium">Sources:</span>{' '}
                      {execution.grounding_sources?.length || 0}
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
