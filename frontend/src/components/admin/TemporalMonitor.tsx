import { useEffect, useState } from 'react'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { ExternalLink } from 'lucide-react'
import { formatDuration } from '@/lib/utils'

interface Workflow {
  workflow_id: string
  run_id: string
  workflow_type: string
  status: string
  start_time: string | null
  close_time: string | null
  execution_time: string | null
  ui_url: string
}

interface Schedule {
  schedule_id: string
  spec: string | null
  paused: boolean
  next_run: string | null
  recent_actions: number
  created_at: string | null
}

export function TemporalMonitor() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadTemporalData()
  }, [])

  const loadTemporalData = async () => {
    try {
      setLoading(true)
      const [workflowsData, schedulesData] = await Promise.all([
        api.getTemporalWorkflows(),
        api.getTemporalSchedules(),
      ])
      setWorkflows(workflowsData.workflows)
      setSchedules(schedulesData.schedules)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load Temporal data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading Temporal data...</div>
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
    <Tabs defaultValue="workflows" className="space-y-4">
      <TabsList>
        <TabsTrigger value="workflows">Workflows</TabsTrigger>
        <TabsTrigger value="schedules">Schedules</TabsTrigger>
      </TabsList>

      <TabsContent value="workflows">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Recent Workflows</CardTitle>
            <CardDescription className="text-sm">Last 24 hours of workflow executions</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Desktop Table View */}
            <div className="hidden md:block">
              <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Workflow ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Duration</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workflows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center text-muted-foreground">
                      No recent workflows
                    </TableCell>
                  </TableRow>
                ) : (
                  workflows.map((workflow) => (
                    <TableRow key={`${workflow.workflow_id}-${workflow.run_id}`}>
                      <TableCell className="font-mono text-xs max-w-xs">
                        <a
                          href={workflow.ui_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 hover:text-primary hover:underline"
                        >
                          <span className="truncate">{workflow.workflow_id}</span>
                          <ExternalLink className="h-3 w-3 flex-shrink-0" />
                        </a>
                      </TableCell>
                      <TableCell className="text-sm">{workflow.workflow_type}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            workflow.status === 'COMPLETED'
                              ? 'default'
                              : workflow.status === 'FAILED'
                                ? 'destructive'
                                : 'secondary'
                          }
                        >
                          {workflow.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs">
                        {workflow.start_time
                          ? formatDistanceToNow(new Date(workflow.start_time), { addSuffix: true })
                          : '-'}
                      </TableCell>
                      <TableCell className="text-xs">
                        {formatDuration(
                          workflow.start_time,
                          workflow.close_time,
                          workflow.status === 'RUNNING' ? 'In progress' : '-'
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            </div>

            {/* Mobile Card View */}
            <div className="block md:hidden space-y-4">
              {workflows.length === 0 ? (
                <p className="text-center text-sm text-muted-foreground py-8">No recent workflows</p>
              ) : (
                workflows.map((workflow) => (
                  <Card key={`${workflow.workflow_id}-${workflow.run_id}`} className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <a
                            href={workflow.ui_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 hover:text-primary hover:underline"
                          >
                            <span className="font-mono text-xs truncate">{workflow.workflow_id}</span>
                            <ExternalLink className="h-3 w-3 flex-shrink-0" />
                          </a>
                          <p className="text-sm text-muted-foreground mt-1">{workflow.workflow_type}</p>
                        </div>
                        <Badge
                          variant={
                            workflow.status === 'COMPLETED'
                              ? 'default'
                              : workflow.status === 'FAILED'
                                ? 'destructive'
                                : 'secondary'
                          }
                          className="text-xs flex-shrink-0"
                        >
                          {workflow.status}
                        </Badge>
                      </div>

                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                        <div>
                          <span className="font-medium">Started:</span>{' '}
                          {workflow.start_time
                            ? formatDistanceToNow(new Date(workflow.start_time), { addSuffix: true })
                            : '-'}
                        </div>
                        <div>
                          <span className="font-medium">Duration:</span>{' '}
                          {formatDuration(
                            workflow.start_time,
                            workflow.close_time,
                            workflow.status === 'RUNNING' ? 'In progress' : '-'
                          )}
                        </div>
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="schedules">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl">Active Schedules</CardTitle>
            <CardDescription className="text-sm">Temporal schedules managing task executions</CardDescription>
          </CardHeader>
          <CardContent>
            {/* Desktop Table View */}
            <div className="hidden md:block">
              <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Schedule ID</TableHead>
                  <TableHead>Cron Spec</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Recent Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {schedules.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground">
                      No active schedules
                    </TableCell>
                  </TableRow>
                ) : (
                  schedules.map((schedule) => (
                    <TableRow key={schedule.schedule_id}>
                      <TableCell className="font-mono text-xs max-w-xs truncate">
                        {schedule.schedule_id}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{schedule.spec || 'N/A'}</TableCell>
                      <TableCell>
                        <Badge variant={schedule.paused ? 'secondary' : 'default'}>
                          {schedule.paused ? 'Paused' : 'Running'}
                        </Badge>
                      </TableCell>
                      <TableCell>{schedule.recent_actions}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
            </div>

            {/* Mobile Card View */}
            <div className="block md:hidden space-y-4">
              {schedules.length === 0 ? (
                <p className="text-center text-sm text-muted-foreground py-8">No active schedules</p>
              ) : (
                schedules.map((schedule) => (
                  <Card key={schedule.schedule_id} className="p-4">
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <p className="font-mono text-xs truncate">{schedule.schedule_id}</p>
                          <p className="font-mono text-xs text-muted-foreground mt-1">
                            {schedule.spec || 'N/A'}
                          </p>
                        </div>
                        <Badge
                          variant={schedule.paused ? 'secondary' : 'default'}
                          className="text-xs flex-shrink-0"
                        >
                          {schedule.paused ? 'Paused' : 'Running'}
                        </Badge>
                      </div>

                      <div className="text-xs text-muted-foreground">
                        <span className="font-medium">Recent Actions:</span>{' '}
                        {schedule.recent_actions}
                      </div>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  )
}
