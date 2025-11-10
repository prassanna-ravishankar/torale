import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Copy, Trash2 } from 'lucide-react'

interface WaitlistEntry {
  id: string
  email: string
  created_at: string
  status: string
}

interface WaitlistEntryCardProps {
  entry: WaitlistEntry
  onCopyEmail: (email: string) => void
  onDelete: (entryId: string) => void
  getStatusBadge: (status: string) => JSX.Element
}

export function WaitlistEntryCard({ entry, onCopyEmail, onDelete, getStatusBadge }: WaitlistEntryCardProps) {
  return (
    <Card className="p-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="font-medium text-sm truncate">{entry.email}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Joined {new Date(entry.created_at).toLocaleDateString()}
            </p>
          </div>
          {getStatusBadge(entry.status)}
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 min-h-[44px]"
            onClick={() => onCopyEmail(entry.email)}
          >
            <Copy className="h-4 w-4 mr-2" />
            Copy Email
          </Button>
          <Button
            variant="destructive"
            size="sm"
            className="min-h-[44px]"
            onClick={() => onDelete(entry.id)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  )
}
