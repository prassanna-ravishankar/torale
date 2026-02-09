import posthog from 'posthog-js'

let initialized = false

export function initPostHog(userId?: string, userEmail?: string, username?: string) {
  const apiKey = window.CONFIG?.posthogApiKey || import.meta.env.VITE_POSTHOG_API_KEY

  if (!apiKey || initialized) return

  posthog.init(apiKey, {
    api_host: window.CONFIG?.posthogHost || import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com',
    capture_pageview: false,
    capture_pageleave: true,
    session_recording: {
      maskAllInputs: true,
      maskTextSelector: '.posthog-no-capture',
    },
    autocapture: false,
  })

  if (userId && userEmail) {
    posthog.identify(userId, {
      email: userEmail,
      username: username,
    })
  }

  initialized = true
}

export function captureEvent(event: string, properties?: Record<string, any>) {
  if (!initialized) return
  posthog.capture(event, properties)
}

export function resetPostHog() {
  if (!initialized) return
  posthog.reset()
}

export { posthog }
