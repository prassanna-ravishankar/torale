import { useState, useEffect } from 'react'
import { useDebounce } from 'use-debounce'
import { X, Check, AlertCircle, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'

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

  if (!isOpen) return null

  const canSubmit = availability?.available && !isChecking && !isSubmitting

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 m-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-900">Choose Your Username</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
            disabled={isSubmitting}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-slate-600 mb-6">
          You need a username to share tasks publicly. This will be part of your task URLs:{' '}
          <code className="text-sm bg-slate-100 px-1 py-0.5 rounded">
            torale.ai/@{username || 'username'}/task-name
          </code>
        </p>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="username" className="block text-sm font-medium text-slate-700 mb-2">
              Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <span className="text-slate-500">@</span>
              </div>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value.toLowerCase())}
                className="w-full pl-8 pr-10 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="yourname"
                pattern="[a-z][a-z0-9_-]*"
                minLength={3}
                maxLength={30}
                required
                disabled={isSubmitting}
              />
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                {isChecking && <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />}
                {!isChecking && availability?.available && (
                  <Check className="w-5 h-5 text-green-500" />
                )}
                {!isChecking && availability && !availability.available && (
                  <AlertCircle className="w-5 h-5 text-red-500" />
                )}
              </div>
            </div>

            {/* Validation feedback */}
            {username.length > 0 && username.length < 3 && (
              <p className="mt-2 text-sm text-slate-500">
                Username must be at least 3 characters
              </p>
            )}
            {availability && !availability.available && availability.error && (
              <p className="mt-2 text-sm text-red-600">{availability.error}</p>
            )}
            {availability?.available && (
              <p className="mt-2 text-sm text-green-600">Username is available!</p>
            )}
          </div>

          <div className="mb-6 p-3 bg-slate-50 rounded-md">
            <p className="text-sm text-slate-600">
              <strong>Requirements:</strong>
            </p>
            <ul className="text-sm text-slate-600 mt-2 space-y-1 ml-4">
              <li>• 3-30 characters</li>
              <li>• Start with a letter</li>
              <li>• Only lowercase letters, numbers, hyphens, and underscores</li>
            </ul>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-50 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
              {isSubmitting ? 'Setting...' : 'Set Username'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
