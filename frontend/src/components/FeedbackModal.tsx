import { useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { captureEvent } from '@/lib/posthog'
import { sanitizePath } from '@/lib/analytics'
import { toast } from 'sonner'

interface FeedbackModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function FeedbackModal({ open, onOpenChange }: FeedbackModalProps) {
  const [feedback, setFeedback] = useState('')
  const [category, setCategory] = useState<'bug' | 'feature' | 'other'>('other')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)

    captureEvent('feedback_submitted', {
      category,
      feedback_length: feedback.length,
      page: sanitizePath(window.location.pathname),
    })

    // EXCEPTION TO PRIVACY POLICY: Intentionally send feedback text to PostHog.
    // This is user-submitted content through an explicit feedback form, distinct
    // from passively captured task data (search queries, conditions) which are
    // never sent. Users actively choose to share this content.
    captureEvent('user_feedback', {
      $feedback_text: feedback,
      $feedback_category: category,
    })

    toast.success('Feedback sent!', {
      description: 'Thank you for helping us improve Torale',
    })

    setFeedback('')
    setCategory('other')
    setSubmitting(false)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="font-grotesk text-lg">Send Feedback</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-mono mb-2">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as typeof category)}
              className="w-full border-2 border-zinc-200 focus:border-zinc-900 p-2 font-mono text-sm"
            >
              <option value="bug">Bug Report</option>
              <option value="feature">Feature Request</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-mono mb-2">Feedback</label>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Tell us what you think..."
              className="w-full border-2 border-zinc-200 focus:border-zinc-900 p-3 font-sans text-sm min-h-[120px]"
              required
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting || !feedback.trim()}>
              {submitting ? 'Sending...' : 'Send Feedback'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
