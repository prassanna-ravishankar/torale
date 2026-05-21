'use client'

// Client-side landing-examples provider for the App Router tree.
//
// Mirrors src/contexts/LandingExamplesContext.tsx but inlines the public-feed
// fetch instead of pulling in src/lib/api.ts (which depends on Vite's
// import.meta.env and the window.CONFIG runtime shim — neither survives the
// Next.js typechecker). First paint is always the build-time fallback bake,
// post-hydration the provider fires a single fetch to refresh evidence.

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  LANDING_EXAMPLES,
  type LandingExampleSnapshot,
  type LandingSnapshot,
} from '@/data/landingExamples'
import fallbackJson from '@/data/landingExamples.fallback.json'
import { hostOf, paraphraseTool, trimEvidence } from '@/utils/landingExamples'

const FALLBACK = fallbackJson as LandingSnapshot

const CONFIG_BY_ID = new Map(LANDING_EXAMPLES.map((cfg) => [cfg.taskId, cfg]))

type ExampleBySurface = {
  hero: LandingExampleSnapshot[]
  cases: LandingExampleSnapshot[]
}

interface LandingExamplesContextValue {
  snapshot: LandingSnapshot
  hero: LandingExampleSnapshot[]
  cases: LandingExampleSnapshot[]
}

const LandingExamplesContext = createContext<LandingExamplesContextValue | null>(null)

function partition(snapshot: LandingSnapshot): ExampleBySurface {
  return {
    hero: snapshot.examples.filter((e) => e.surfaces.includes('hero')),
    cases: snapshot.examples.filter((e) => e.surfaces.includes('cases')),
  }
}

interface FeedExecutionLike {
  task_id: string
  status?: string
  started_at?: string
  notification?: string
  result?: {
    evidence?: string
    activity?: { tool?: string; detail?: string }[]
    sources?: { url: string; title?: string }[]
    grounding_sources?: { url: string; title?: string }[]
  }
  grounding_sources?: { url: string; title?: string }[]
}

function mergeExecution(
  baked: LandingExampleSnapshot,
  exec: FeedExecutionLike,
): LandingExampleSnapshot {
  const cfg = CONFIG_BY_ID.get(baked.taskId)
  const liveEvidence = exec.result?.evidence || exec.notification || ''
  const evidence =
    trimEvidence(cfg?.displayEvidenceOverride || liveEvidence) || baked.evidence

  const activity = (exec.result?.activity || [])
    .filter((a) => a.tool)
    .slice(0, 3)
    .map((a) => ({
      verb: paraphraseTool(a.tool),
      detail: (a.detail || '').replace(/\s+/g, ' ').trim().slice(0, 80),
    }))

  const sourceList =
    exec.result?.sources || exec.grounding_sources || exec.result?.grounding_sources || []
  const seen = new Set<string>()
  const sources: string[] = []
  for (const s of sourceList) {
    const h = hostOf(s)
    if (h && !seen.has(h)) {
      seen.add(h)
      sources.push(h)
      if (sources.length >= 3) break
    }
  }

  return {
    ...baked,
    startedAt: exec.started_at || baked.startedAt,
    evidence,
    activity: activity.length > 0 ? activity : baked.activity,
    sources: sources.length > 0 ? sources : baked.sources,
  }
}

export function LandingExamplesProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<LandingSnapshot>(FALLBACK)

  useEffect(() => {
    let cancelled = false
    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
    const url = `${apiBase}/api/v1/public/feed?limit=100`

    fetch(url)
      .then((r) => (r.ok ? r.json() : null))
      .then((feed) => {
        if (cancelled || !Array.isArray(feed)) return
        const latestByTask = new Map<string, FeedExecutionLike>()
        for (const exec of feed as FeedExecutionLike[]) {
          if (!exec?.task_id || exec.status !== 'success') continue
          if (!CONFIG_BY_ID.has(exec.task_id)) continue
          const prior = latestByTask.get(exec.task_id)
          if (
            !prior ||
            new Date(exec.started_at || 0) > new Date(prior.started_at || 0)
          ) {
            latestByTask.set(exec.task_id, exec)
          }
        }
        if (latestByTask.size === 0) return
        setSnapshot((prev) => ({
          ...prev,
          examples: prev.examples.map((entry) => {
            const exec = latestByTask.get(entry.taskId)
            return exec ? mergeExecution(entry, exec) : entry
          }),
        }))
      })
      .catch(() => {
        // Swallow — marketing surfaces must not surface fetch errors.
      })

    return () => {
      cancelled = true
    }
  }, [])

  const value = useMemo<LandingExamplesContextValue>(() => {
    const { hero, cases } = partition(snapshot)
    return { snapshot, hero, cases }
  }, [snapshot])

  return (
    <LandingExamplesContext.Provider value={value}>
      {children}
    </LandingExamplesContext.Provider>
  )
}

export function useLandingExamples(): LandingExamplesContextValue {
  const ctx = useContext(LandingExamplesContext)
  if (!ctx) {
    const { hero, cases } = partition(FALLBACK)
    return { snapshot: FALLBACK, hero, cases }
  }
  return ctx
}
