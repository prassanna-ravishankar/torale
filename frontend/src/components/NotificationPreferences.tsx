'use client'

import { useState } from 'react'
import { useNotifications } from '@/hooks/useNotifications'

export function NotificationPreferences() {
  const { 
    preferences, 
    updatePreferences, 
    requestNotificationPermission,
    loading,
    error 
  } = useNotifications()
  
  const [saving, setSaving] = useState(false)

  const handleToggleEmail = async () => {
    if (!preferences) return
    
    setSaving(true)
    await updatePreferences({
      email_enabled: !preferences.email_enabled
    })
    setSaving(false)
  }

  const handleFrequencyChange = async (frequency: string) => {
    setSaving(true)
    await updatePreferences({
      email_frequency: frequency as any
    })
    setSaving(false)
  }

  const handleToggleBrowser = async () => {
    if (!preferences) return
    
    setSaving(true)
    
    // If enabling browser notifications, request permission first
    if (!preferences.browser_enabled) {
      const granted = await requestNotificationPermission()
      if (!granted) {
        setSaving(false)
        return
      }
    }
    
    await updatePreferences({
      browser_enabled: !preferences.browser_enabled
    })
    setSaving(false)
  }

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading notification preferences: {error}</p>
      </div>
    )
  }

  const isNotificationSupported = typeof window !== 'undefined' && 'Notification' in window
  const browserPermission = isNotificationSupported ? Notification.permission : 'denied'

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Notification Preferences
        </h3>
        
        {/* Email Notifications */}
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="font-medium text-gray-900">Email Notifications</h4>
              <p className="text-sm text-gray-600">
                Receive alerts via email when content changes are detected
              </p>
            </div>
            <button
              onClick={handleToggleEmail}
              disabled={saving}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                preferences?.email_enabled 
                  ? 'bg-indigo-600' 
                  : 'bg-gray-200'
              } ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  preferences?.email_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Email Frequency */}
          {preferences?.email_enabled && (
            <div className="ml-4 space-y-2">
              <label className="text-sm font-medium text-gray-700">
                Email Frequency
              </label>
              <div className="space-y-2">
                {[
                  { value: 'immediate', label: 'Immediate', description: 'Send emails as soon as changes are detected' },
                  { value: 'hourly', label: 'Hourly', description: 'Send a summary every hour' },
                  { value: 'daily', label: 'Daily', description: 'Send a daily summary' }
                ].map((option) => (
                  <label key={option.value} className="flex items-start space-x-3">
                    <input
                      type="radio"
                      name="frequency"
                      value={option.value}
                      checked={preferences?.email_frequency === option.value}
                      onChange={() => handleFrequencyChange(option.value)}
                      disabled={saving}
                      className="mt-0.5 h-4 w-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
                    />
                    <div>
                      <div className="text-sm font-medium text-gray-900">{option.label}</div>
                      <div className="text-xs text-gray-600">{option.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Browser Notifications */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <h4 className="font-medium text-gray-900">Browser Notifications</h4>
            <p className="text-sm text-gray-600">
              Show desktop notifications in your browser
            </p>
            {!isNotificationSupported && (
              <p className="text-xs text-red-600 mt-1">
                Browser notifications are not supported in this browser
              </p>
            )}
            {isNotificationSupported && browserPermission === 'denied' && (
              <p className="text-xs text-orange-600 mt-1">
                Browser notifications are blocked. Please enable them in your browser settings.
              </p>
            )}
          </div>
          <button
            onClick={handleToggleBrowser}
            disabled={saving || !isNotificationSupported}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
              preferences?.browser_enabled && isNotificationSupported
                ? 'bg-indigo-600' 
                : 'bg-gray-200'
            } ${saving || !isNotificationSupported ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences?.browser_enabled && isNotificationSupported ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {saving && (
        <div className="text-sm text-gray-600 flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600 mr-2"></div>
          Saving preferences...
        </div>
      )}
    </div>
  )
}