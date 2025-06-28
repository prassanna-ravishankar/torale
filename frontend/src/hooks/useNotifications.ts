'use client'

/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabaseClient'
import axiosInstance from '@/lib/axiosInstance'
import type { RealtimeChannel } from '@supabase/supabase-js'

export interface NotificationAlert {
  id: string
  monitored_source_id: string
  user_id: string
  detected_at: string
  change_summary: string
  change_details: Record<string, unknown>
  is_acknowledged: boolean
  notification_sent: boolean
  notification_sent_at?: string
}

export interface NotificationPreferences {
  id: string
  user_id: string
  user_email: string
  email_enabled: boolean
  email_frequency: 'immediate' | 'hourly' | 'daily' | 'disabled'
  browser_enabled: boolean
  created_at: string
  updated_at: string
}

export interface NotificationStats {
  total_alerts: number
  sent_notifications: number
  failed_notifications: number
  pending_notifications: number
}

export function useNotifications() {
  const [alerts, setAlerts] = useState<NotificationAlert[]>([])
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null)
  const [stats, setStats] = useState<NotificationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [channel, setChannel] = useState<RealtimeChannel | null>(null)


  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        
        // Get current user
        const { data: { user } } = await supabase.auth.getUser()
        if (!user) {
          setError('User not authenticated')
          return
        }

        // Fetch alerts
        const { data: alertsData, error: alertsError } = await (supabase as any)
          .from('change_alerts')
          .select('*')
          .eq('user_id', user.id)
          .order('detected_at', { ascending: false })
          .limit(50)

        if (alertsError) throw alertsError
        setAlerts(alertsData || [])

        // Fetch preferences via backend API
        try {
          const prefsResponse = await axiosInstance.get('/notifications/preferences')
          setPreferences(prefsResponse.data)
        } catch (prefsError) {
          console.warn('Could not fetch notification preferences:', prefsError)
        }

        // Fetch stats via backend API
        try {
          const statsResponse = await axiosInstance.get('/notifications/stats')
          setStats(statsResponse.data)
        } catch (statsError) {
          console.warn('Could not fetch notification stats:', statsError)
        }

      } catch (err) {
        console.error('Error fetching notification data:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Set up real-time subscription
  useEffect(() => {
    const setupRealtimeSubscription = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      // Subscribe to changes in change_alerts table for the current user
      const alertsChannel = (supabase as any)
        .channel('change_alerts')
        .on(
          'postgres_changes',
          {
            event: 'INSERT',
            schema: 'public',
            table: 'change_alerts',
            filter: `user_id=eq.${user.id}`
          },
          (payload: any) => {
            console.log('New alert received:', payload)
            const newAlert = payload.new as NotificationAlert
            
            setAlerts(prev => [newAlert, ...prev])
            
            // Show browser notification if enabled
            if (preferences?.browser_enabled && 'Notification' in window) {
              if (Notification.permission === 'granted') {
                new Notification('🔔 Content Change Detected', {
                  body: newAlert.change_summary,
                  icon: '/favicon.ico',
                  tag: newAlert.id
                })
              }
            }
            
            // Update stats
            setStats(prev => prev ? {
              ...prev,
              total_alerts: prev.total_alerts + 1,
              pending_notifications: prev.pending_notifications + 1
            } : null)
          }
        )
        .on(
          'postgres_changes',
          {
            event: 'UPDATE',
            schema: 'public',
            table: 'change_alerts',
            filter: `user_id=eq.${user.id}`
          },
          (payload: any) => {
            console.log('Alert updated:', payload)
            const updatedAlert = payload.new as NotificationAlert
            
            setAlerts(prev => prev.map(alert => 
              alert.id === updatedAlert.id ? updatedAlert : alert
            ))
          }
        )
        .subscribe()

      setChannel(alertsChannel)
    }

    if (!loading && preferences !== null) {
      setupRealtimeSubscription()
    }

    return () => {
      if (channel) {
        (supabase as any).removeChannel(channel)
      }
    }
  }, [loading, preferences, channel])

  // Request browser notification permission
  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      const permission = await Notification.requestPermission()
      return permission === 'granted'
    }
    return Notification.permission === 'granted'
  }

  // Update notification preferences via backend API
  const updatePreferences = async (updates: Partial<NotificationPreferences>) => {
    try {
      const response = await axiosInstance.put('/notifications/preferences', updates)
      const result = response.data
      
      if (result.success) {
        // Refetch preferences to get updated data
        const prefsResponse = await axiosInstance.get('/notifications/preferences')
        setPreferences(prefsResponse.data)
      }

      return result.success
    } catch (err) {
      console.error('Error updating preferences:', err)
      setError(err instanceof Error ? err.message : 'Failed to update preferences')
      return false
    }
  }

  // Acknowledge an alert
  const acknowledgeAlert = async (alertId: string) => {
    try {
      const { error } = await (supabase as any)
        .from('change_alerts')
        .update({ 
          is_acknowledged: true,
          acknowledged_at: new Date().toISOString()
        })
        .eq('id', alertId)
        .select()
        .single()

      if (error) throw error

      setAlerts(prev => prev.map(alert => 
        alert.id === alertId ? { ...alert, is_acknowledged: true } : alert
      ))

      return true
    } catch (err) {
      console.error('Error acknowledging alert:', err)
      setError(err instanceof Error ? err.message : 'Failed to acknowledge alert')
      return false
    }
  }

  // Manually trigger notification for an alert via backend API
  const resendNotification = async (alertId: string, forceResend: boolean = false) => {
    try {
      const response = await axiosInstance.post('/notifications/send', {
        alert_id: alertId,
        force_resend: forceResend
      })

      return response.data.success
    } catch (err) {
      console.error('Error resending notification:', err)
      setError(err instanceof Error ? err.message : 'Failed to resend notification')
      return false
    }
  }

  return {
    alerts,
    preferences,
    stats,
    loading,
    error,
    updatePreferences,
    acknowledgeAlert,
    resendNotification,
    requestNotificationPermission,
    clearError: () => setError(null)
  }
}