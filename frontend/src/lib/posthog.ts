import posthog from 'posthog-js'

let initialized = false

export function initPostHog(userId?: string) {
  const apiKey = window.CONFIG?.posthogApiKey || import.meta.env.VITE_POSTHOG_API_KEY

  if (!apiKey) return

  try {
    if (!initialized) {
      posthog.init(apiKey, {
        api_host: window.CONFIG?.posthogHost || import.meta.env.VITE_POSTHOG_HOST || 'https://eu.posthog.com',
        capture_pageview: false,
        capture_pageleave: true,
        session_recording: {
          maskAllInputs: true,
          maskTextSelector: '.posthog-no-capture',
        },
        autocapture: false,
      })
      initialized = true
    }

    // Identify or re-identify if userId provided
    if (userId) {
      posthog.identify(userId)
    }
  } catch (error) {
    console.error('PostHog initialization failed - analytics disabled:', error)
    // Don't set initialized = true, so future capture calls will no-op
  }
}

export function captureEvent(event: string, properties?: Record<string, any>) {
  if (!initialized) return

  try {
    posthog.capture(event, properties)
  } catch (error) {
    // Never let analytics break user interactions
    console.warn(`PostHog event capture failed for '${event}':`, error)
  }
}

export function resetPostHog() {
  if (!initialized) return

  try {
    posthog.reset()
  } catch (error) {
    console.warn('PostHog reset failed:', error)
    // Continue anyway - don't block user from signing out
  }
}

export { posthog }
