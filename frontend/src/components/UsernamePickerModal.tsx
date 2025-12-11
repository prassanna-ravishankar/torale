import { useState, useEffect } from 'react'
import { useDebounce } from 'use-debounce'
import { Check, AlertCircle, Loader2, AlertTriangle } from 'lucide-react'
import { api } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

interface UsernamePickerModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (username: string) => void
}

export function UsernamePickerModal({ isOpen, onClose, onSuccess }: UsernamePickerModalProps) {
  const { syncUser } = useAuth()
  const [username, setUsername] = useState('')
  const [debouncedUsername] = useDebounce(username, 500)
  const [isChecking, setIsChecking] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [availability, setAvailability] = useState<{
    available: boolean
    error: string | null
  } | null>(null)

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setUsername('')
      setAvailability(null)
    }
  }, [isOpen])

  // Check username availability when debounced value changes
  useEffect(() => {
    if (!debouncedUsername || debouncedUsername.length < 3) {
      setAvailability(null)
      return
    }

    const checkAvailability = async () => {
      setIsChecking(true)
      try {
        const result = await api.checkUsernameAvailability(debouncedUsername)
        setAvailability(result)
      } catch (error) {
        setAvailability({ available: false, error: 'Failed to check availability' })
      } finally {
        setIsChecking(false)
      }
    }

    checkAvailability()
  }, [debouncedUsername])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!availability?.available) return

    setIsSubmitting(true)
    try {
      const result = await api.setUsername(username)

      // Refresh user context to get the new username
      if (syncUser) {
        await syncUser()
      }

      onSuccess(result.username)
      onClose()
    } catch (error) {
      setAvailability({
        available: false,
        error: error instanceof Error ? error.message : 'Failed to set username',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const canSubmit = availability?.available && !isChecking && !isSubmitting

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md border-2 border-zinc-900 shadow-brutalist rounded-none p-0">
        <DialogHeader className="p-6 pb-4 border-b-2 border-zinc-200">
          <DialogTitle className="text-xl font-bold font-grotesk text-zinc-900">
            Choose Your Username
          </DialogTitle>
          <DialogDescription className="text-zinc-600">
            You need a username to share tasks publicly. This will be part of your task URLs:{' '}
            <code className="text-sm bg-zinc-100 border border-zinc-200 px-1.5 py-0.5 font-mono">
              torale.ai/t/{username || 'username'}/task-name
            </code>
          </DialogDescription>
        </DialogHeader>

        {/* Permanent username warning */}
        <div className="mx-6 mt-4 p-4 bg-amber-50 border-2 border-amber-400">
          <div className="flex gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-bold text-amber-900 mb-1">Username is permanent</p>
              <p className="text-amber-800">
                Choose carefully! You cannot change your username after setting it. This prevents your public task links from breaking.
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 pt-4">
          <div className="mb-4">
            <label htmlFor="username-input" className="block text-sm font-medium text-zinc-700 mb-2">
              Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-zinc-500 font-mono">@</span>
              </div>
              <input
                id="username-input"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value.toLowerCase())}
                className="w-full pl-8 pr-10 py-2.5 border-2 border-zinc-300 bg-white focus:outline-none focus:border-zinc-900 focus:ring-0 font-mono transition-colors"
                placeholder="yourname"
                pattern="[a-z][a-z0-9_-]*"
                minLength={3}
                maxLength={30}
                required
                disabled={isSubmitting}
                autoFocus
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                {isChecking && <Loader2 className="w-5 h-5 text-zinc-400 animate-spin" />}
                {!isChecking && availability?.available && (
                  <Check className="w-5 h-5 text-green-600" />
                )}
                {!isChecking && availability && !availability.available && (
                  <AlertCircle className="w-5 h-5 text-red-600" />
                )}
              </div>
            </div>

            {/* Validation feedback */}
            {username.length > 0 && username.length < 3 && (
              <p className="mt-2 text-sm text-zinc-500">
                Username must be at least 3 characters
              </p>
            )}
            {availability && !availability.available && availability.error && (
              <p className="mt-2 text-sm text-red-600 font-medium">{availability.error}</p>
            )}
            {availability?.available && (
              <p className="mt-2 text-sm text-green-600 font-medium">Username is available!</p>
            )}
          </div>

          <div className="mb-6 p-4 bg-zinc-50 border-2 border-zinc-200">
            <p className="text-sm font-medium text-zinc-700 mb-2">Requirements:</p>
            <ul className="text-sm text-zinc-600 space-y-1">
              <li className="flex items-center gap-2">
                <span className="w-1 h-1 bg-zinc-400 rounded-full"></span>
                3-30 characters
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1 h-1 bg-zinc-400 rounded-full"></span>
                Start with a letter
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1 h-1 bg-zinc-400 rounded-full"></span>
                Only lowercase letters, numbers, hyphens, and underscores
              </li>
            </ul>
          </div>

          <DialogFooter className="gap-3 sm:gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting}
              className="flex-1 border-2 border-zinc-300 hover:border-zinc-900 rounded-none"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!canSubmit}
              className="flex-1 bg-zinc-900 text-white border-2 border-zinc-900 hover:bg-zinc-800 rounded-none"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
              {isSubmitting ? 'Setting...' : 'Set Username'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
