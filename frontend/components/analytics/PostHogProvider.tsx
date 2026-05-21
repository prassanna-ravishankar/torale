'use client'

import { Suspense, useEffect, type ReactNode } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'

// Lazy PostHog provider for the Next.js tree.
// - Init runs on first interaction (or 10s fallback) to keep the SDK off the
//   LCP critical path, mirroring the Vite-era pattern at src/lib/posthog.ts.
// - Pageview tracking via usePathname + useSearchParams in a useEffect.
//   The Suspense boundary is mandatory: Next 15 requires useSearchParams
//   consumers to be wrapped or builds fail with the "missing-suspense" error.

const INTERACTION_EVENTS = [
  'pointerdown',
  'touchstart',
  'keydown',
  'scroll',
  'visibilitychange',
] as const

const FALLBACK_TIMEOUT_MS = 10000

type PostHog = typeof import('posthog-js').default

let posthogPromise: Promise<PostHog> | null = null
let initialized = false
let triggerScheduled = false
let apiKey: string | undefined
type QueuedEvent = { event: string; properties?: Record<string, unknown> }
const eventQueue: QueuedEvent[] = []

function loadPostHog(): Promise<PostHog> {
  if (!posthogPromise) {
    posthogPromise = import('posthog-js').then((m) => m.default)
  }
  return posthogPromise
}

async function boot() {
  if (initialized || !apiKey) return
  try {
    const posthog = await loadPostHog()
    if (initialized) return
    posthog.init(apiKey, {
      api_host:
        process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://eu.posthog.com',
      capture_pageview: false,
      capture_pageleave: true,
      session_recording: {
        maskAllInputs: true,
        maskTextSelector: '.posthog-no-capture',
      },
      autocapture: false,
    })
    initialized = true
    while (eventQueue.length > 0) {
      const next = eventQueue.shift()
      if (next) posthog.capture(next.event, next.properties)
    }
  } catch (error) {
    // Swallow: analytics failure must never break marketing rendering.
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
    for (const name of INTERACTION_EVENTS) {
      window.removeEventListener(name, fire)
    }
    clearTimeout(fallbackId)
    void boot()
  }

  for (const name of INTERACTION_EVENTS) {
    window.addEventListener(name, fire, { once: true, passive: true })
  }
  const fallbackId = window.setTimeout(fire, FALLBACK_TIMEOUT_MS)
}

function captureEvent(event: string, properties?: Record<string, unknown>) {
  if (!apiKey) return
  if (!initialized || !posthogPromise) {
    eventQueue.push({ event, properties })
    return
  }
  posthogPromise
    .then((posthog) => posthog.capture(event, properties))
    .catch(() => {
      // ignore — analytics shouldn't surface user-visible errors
    })
}

function sanitizePath(path: string): string {
  // Best-effort UUID redaction to keep PII out of the pageview path field.
  return path.replace(
    /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi,
    ':id',
  )
}

function PageviewTracker() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    apiKey = process.env.NEXT_PUBLIC_POSTHOG_API_KEY
    if (!apiKey) return
    scheduleBoot()
  }, [])

  useEffect(() => {
    if (!pathname) return
    const query = searchParams?.toString()
    const path = query ? `${pathname}?${query}` : pathname
    captureEvent('$pageview', { path: sanitizePath(path) })
  }, [pathname, searchParams])

  return null
}

export function PostHogProvider({ children }: { children: ReactNode }) {
  return (
    <>
      <Suspense fallback={null}>
        <PageviewTracker />
      </Suspense>
      {children}
    </>
  )
}

export default PostHogProvider
