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
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { QueryCard } from './cards/QueryCard'
import { CronDisplay } from '@/components/ui/CronDisplay'

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
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading queries...</div>
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
            <CardTitle className="text-lg sm:text-xl">All User Queries</CardTitle>
            <CardDescription className="text-sm">Monitor all search queries and conditions across users</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Switch id="active-only" checked={activeOnly} onCheckedChange={setActiveOnly} />
            <Label htmlFor="active-only" className="text-sm whitespace-nowrap">Active only</Label>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Desktop Table View */}
        <div className="hidden md:block">
          <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Search Query</TableHead>
              <TableHead>Condition</TableHead>
              <TableHead>Schedule</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Executions</TableHead>
              <TableHead>Triggered</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {queries.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-muted-foreground">
                  No queries found
                </TableCell>
              </TableRow>
            ) : (
              queries.map((query) => (
                <TableRow key={query.id}>
                  <TableCell className="font-mono text-xs">{query.user_email}</TableCell>
                  <TableCell className="font-medium">{query.name}</TableCell>
                  <TableCell className="max-w-xs truncate">{query.search_query}</TableCell>
                  <TableCell className="max-w-xs truncate text-sm text-muted-foreground">
                    {query.condition_description}
                  </TableCell>
                  <TableCell className="text-xs">
                    <CronDisplay cron={query.schedule} showRaw={false} className="text-xs" />
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Badge variant={query.is_active ? 'default' : 'secondary'}>
                        {query.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                      {query.condition_met && (
                        <Badge variant="outline" className="text-green-600">
                          Met
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{query.execution_count}</TableCell>
                  <TableCell>{query.trigger_count}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        </div>

        {/* Mobile Card View */}
        <div className="block md:hidden space-y-4">
          {queries.length === 0 ? (
            <p className="text-center text-sm text-muted-foreground py-8">No queries found</p>
          ) : (
            queries.map((query) => <QueryCard key={query.id} query={query} />)
          )}
        </div>
      </CardContent>
    </Card>
  )
}
