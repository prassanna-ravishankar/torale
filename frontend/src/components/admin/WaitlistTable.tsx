import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Loader2, Users, Copy, Trash2, CheckCircle } from 'lucide-react'
import { toast } from 'sonner'

interface WaitlistEntry {
  id: string
  email: string
  created_at: string
  status: string
  invited_at: string | null
  notes: string | null
}

interface WaitlistStats {
  pending: number
  invited: number
  converted: number
  total: number
}

export function WaitlistTable() {
  const [entries, setEntries] = useState<WaitlistEntry[]>([])
  const [stats, setStats] = useState<WaitlistStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  useEffect(() => {
    loadWaitlist()
    loadStats()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter])

  const loadWaitlist = async () => {
    try {
      setLoading(true)
      const data = await api.getWaitlist(statusFilter || undefined)
      setEntries(data)
    } catch (error) {
      console.error('Failed to load waitlist:', error)
      toast.error('Failed to load waitlist')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const data = await api.getWaitlistStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const deleteEntry = async (entryId: string) => {
    if (!confirm('Are you sure you want to remove this entry?')) return

    try {
      await api.deleteWaitlistEntry(entryId)
      toast.success('Entry removed')
      loadWaitlist()
      loadStats()
    } catch (error) {
      console.error('Failed to delete entry:', error)
      toast.error('Failed to remove entry')
    }
  }

  const copyEmail = (email: string) => {
    navigator.clipboard.writeText(email)
    toast.success('Email copied to clipboard')
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "success"> = {
      pending: 'default',
      invited: 'secondary',
      converted: 'success',
    }

    return (
      <Badge variant={variants[status] || 'default'}>
        {status}
      </Badge>
    )
  }

  if (loading && !entries.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.pending}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Converted</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.converted}</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Waitlist Entries</CardTitle>
          <CardDescription>Manage users waiting for access</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 mb-4">
            <Button
              variant={statusFilter === null ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter(null)}
            >
              All
            </Button>
            <Button
              variant={statusFilter === 'pending' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('pending')}
            >
              Pending
            </Button>
            <Button
              variant={statusFilter === 'converted' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setStatusFilter('converted')}
            >
              Converted
            </Button>
          </div>

          {entries.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No waitlist entries found
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Joined</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {entry.email}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyEmail(entry.email)}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </TableCell>
                    <TableCell>
                      {new Date(entry.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>{getStatusBadge(entry.status)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteEntry(entry.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
