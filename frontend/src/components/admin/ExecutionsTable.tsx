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
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Execution History</CardTitle>
            <CardDescription>View all task executions across users</CardDescription>
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[180px]">
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
      </CardContent>
    </Card>
  )
}
