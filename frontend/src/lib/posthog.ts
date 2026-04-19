// PostHog is dynamically imported so the ~60 KiB SDK plus its remote
// `array/config.js` (~800 ms of render-blocking time on mobile) are kept
// off the critical path. We delay loading until the first genuine user
// interaction, with a fallback timeout so we still capture short sessions.
type PostHog = typeof import('posthog-js').default

type QueuedEvent = { event: string; properties?: Record<string, unknown> }

const INTERACTION_EVENTS = [
  'pointerdown',
  'touchstart',
  'keydown',
  'scroll',
  'visibilitychange',
] as const

// Fallback trigger if the user never interacts (e.g. bot, quick bounce).
// Still well after LCP so it doesn't pollute perf metrics.
const FALLBACK_TIMEOUT_MS = 10000

let posthogPromise: Promise<PostHog> | null = null
let initialized = false
let pendingUserId: string | undefined
let triggerScheduled = false
const eventQueue: QueuedEvent[] = []
let apiKey: string | undefined

function loadPostHog(): Promise<PostHog> {
  if (!posthogPromise) {
    posthogPromise = import('posthog-js').then((m) => m.default)
  }
  return posthogPromise
}

function detachListeners(handler: () => void) {
  for (const name of INTERACTION_EVENTS) {
    window.removeEventListener(name, handler)
  }
}

async function boot() {
  if (initialized || !apiKey) return
  try {
    const posthog = await loadPostHog()
    if (initialized) return
    posthog.init(apiKey, {
      api_host:
        window.CONFIG?.posthogHost ||
        import.meta.env.VITE_POSTHOG_HOST ||
        'https://eu.posthog.com',
      capture_pageview: false,
      capture_pageleave: true,
      session_recording: {
        maskAllInputs: true,
        maskTextSelector: '.posthog-no-capture',
      },
      autocapture: false,
    })
    initialized = true
    if (pendingUserId) {
      posthog.identify(pendingUserId)
    }
    while (eventQueue.length > 0) {
      const next = eventQueue.shift()!
      posthog.capture(next.event, next.properties)
    }
  } catch (error) {
    console.error('PostHog initialization failed - analytics disabled:', error)
  }
}

function scheduleBoot() {
  if (triggerScheduled || typeof window === 'undefined') return
  triggerScheduled = true

  let fired = false
  const fire = () => {
    if (fired) return
    fired = true
    detachListeners(fire)
    clearTimeout(fallbackId)
    void boot()
  }

  for (const name of INTERACTION_EVENTS) {
    window.addEventListener(name, fire, { once: true, passive: true })
  }
  const fallbackId = window.setTimeout(fire, FALLBACK_TIMEOUT_MS)
}

export function initPostHog(userId?: string) {
  apiKey = window.CONFIG?.posthogApiKey || import.meta.env.VITE_POSTHOG_API_KEY
  if (!apiKey) return

  if (userId) {
    pendingUserId = userId
  }

  if (initialized && posthogPromise) {
    if (userId) {
      void posthogPromise.then((posthog) => posthog.identify(userId))
    }
    return
  }

  scheduleBoot()
}

export function captureEvent(event: string, properties?: Record<string, unknown>) {
  if (!apiKey) return

  if (!initialized || !posthogPromise) {
    eventQueue.push({ event, properties })
    return
  }

  posthogPromise
    .then((posthog) => posthog.capture(event, properties))
    .catch((error) => {
      console.warn(`PostHog event capture failed for '${event}':`, error)
    })
}

export function resetPostHog() {
  pendingUserId = undefined
  if (!initialized || !posthogPromise) return

  posthogPromise
    .then((posthog) => posthog.reset())
    .catch((error) => {
      console.warn('PostHog reset failed:', error)
    })
}
