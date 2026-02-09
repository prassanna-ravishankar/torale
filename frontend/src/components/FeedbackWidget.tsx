import { useState } from 'react'
import { ThumbsUp, ThumbsDown } from 'lucide-react'
import { captureEvent } from '@/lib/posthog'
import { sanitizePath } from '@/lib/analytics'
import { cn } from '@/lib/utils'

interface FeedbackWidgetProps {
  context: string
  contextId?: string
  compact?: boolean
}

export function FeedbackWidget({ context, contextId, compact = false }: FeedbackWidgetProps) {
  const [voted, setVoted] = useState<'positive' | 'negative' | null>(null)

  const handleVote = (sentiment: 'positive' | 'negative') => {
    setVoted(sentiment)

    captureEvent('feedback_widget_interaction', {
      context,
      context_id: contextId,
      sentiment,
      page: sanitizePath(window.location.pathname),
    })
  }

  return (
    <div className="flex items-center gap-2">
      {voted ? (
        <span className="text-xs text-zinc-500 font-mono">Thanks for your feedback!</span>
      ) : (
        <>
          <button
            onClick={() => handleVote('positive')}
            className={cn(
              'border-2 border-zinc-200 hover:border-zinc-900 transition-colors',
              compact ? 'p-1' : 'p-2'
            )}
            aria-label="Thumbs up"
          >
            <ThumbsUp className={cn(compact ? 'h-3 w-3' : 'h-4 w-4')} />
          </button>
          <button
            onClick={() => handleVote('negative')}
            className={cn(
              'border-2 border-zinc-200 hover:border-zinc-900 transition-colors',
              compact ? 'p-1' : 'p-2'
            )}
            aria-label="Thumbs down"
          >
            <ThumbsDown className={cn(compact ? 'h-3 w-3' : 'h-4 w-4')} />
          </button>
        </>
      )}
    </div>
  )
}
