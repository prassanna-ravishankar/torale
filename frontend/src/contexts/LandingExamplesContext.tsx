'use client';

// Single source of post-hydration revalidated landing-page watch state.
//
// First paint: returns the build-time snapshot baked by
// scripts/sync-landing-examples.mjs (committed fallback at
// src/data/landingExamples.fallback.json). This keeps prerender HTML and
// React first paint structurally identical, avoiding hydration mismatches.
//
// Post-hydration: the provider fires a single fetch against
// /api/v1/public/feed and merges fresher executions into the in-memory
// snapshot keyed by taskId. The "watching · N conditions" count chip
// stays as whatever the build-time bake captured because the bake
// reads prod cross-env while the runtime API client is per-env (see
// the useEffect comment below for the full reasoning). Both Hero
// (rotation) and Cases (Receipts) read from this context so a rogue
// task on /explore can't surface twice.

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { LANDING_EXAMPLES, type LandingSnapshot, type LandingExampleSnapshot } from '@/data/landingExamples';
import fallbackJson from '@/data/landingExamples.fallback.json';
import { hostOf, paraphraseTool, trimEvidence } from '@/utils/landingExamples';
import { publicApi } from '@/lib/publicApi';

const FALLBACK = fallbackJson as LandingSnapshot;

// Build once at module init for O(1) lookup inside mergeExecution (which
// itself runs inside a map() loop). Was a .find() per merge — fine for 7
// entries but cleaner this way and removes a future-scale footgun
// (gemini #uN).
const CONFIG_BY_ID = new Map(LANDING_EXAMPLES.map((cfg) => [cfg.taskId, cfg]));

type ExampleBySurface = {
  hero: LandingExampleSnapshot[];
  cases: LandingExampleSnapshot[];
};

interface LandingExamplesContextValue {
  snapshot: LandingSnapshot;
  hero: LandingExampleSnapshot[];
  cases: LandingExampleSnapshot[];
}

const LandingExamplesContext = createContext<LandingExamplesContextValue | null>(null);

function partition(snapshot: LandingSnapshot): ExampleBySurface {
  return {
    hero: snapshot.examples.filter((e) => e.surfaces.includes('hero')),
    cases: snapshot.examples.filter((e) => e.surfaces.includes('cases')),
  };
}

interface FeedExecutionLike {
  task_id: string;
  status?: string;
  started_at?: string;
  notification?: string;
  result?: {
    evidence?: string;
    activity?: { tool?: string; detail?: string }[];
    sources?: { url: string; title?: string }[];
    grounding_sources?: { url: string; title?: string }[];
  };
  grounding_sources?: { url: string; title?: string }[];
}

/**
 * Merge a fresh execution into a baked snapshot entry. Mirrors the field
 * extraction the build script does so live + baked entries have identical
 * shape. Returns the baked entry untouched if the live fetch yielded
 * nothing useful for a slot.
 */
function mergeExecution(
  baked: LandingExampleSnapshot,
  exec: FeedExecutionLike,
): LandingExampleSnapshot {
  const cfg = CONFIG_BY_ID.get(baked.taskId);
  const liveEvidence = exec.result?.evidence || exec.notification || '';
  const evidence = trimEvidence(cfg?.displayEvidenceOverride || liveEvidence) || baked.evidence;

  const activity = (exec.result?.activity || [])
    .filter((a) => a.tool)
    .slice(0, 3)
    .map((a) => ({
      verb: paraphraseTool(a.tool),
      detail: (a.detail || '').replace(/\s+/g, ' ').trim().slice(0, 80),
    }));

  const sourceList = exec.result?.sources || exec.grounding_sources || exec.result?.grounding_sources || [];
  const seen = new Set<string>();
  const sources: string[] = [];
  for (const s of sourceList) {
    const h = hostOf(s);
    if (h && !seen.has(h)) {
      seen.add(h);
      sources.push(h);
      if (sources.length >= 3) break;
    }
  }

  return {
    ...baked,
    startedAt: exec.started_at || baked.startedAt,
    evidence,
    activity: activity.length > 0 ? activity : baked.activity,
    sources: sources.length > 0 ? sources : baked.sources,
  };
}

export function LandingExamplesProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<LandingSnapshot>(FALLBACK);

  useEffect(() => {
    let cancelled = false;
    // Only refresh the per-watch evidence here. We deliberately do NOT
    // refresh `totalPublicConditions` post-hydration: the bake is
    // cross-env (always reads the prod public feed at build, see
    // sync-landing-examples.mjs), but the runtime API client uses
    // NEXT_PUBLIC_API_BASE_URL — which on staging points at api-staging
    // (0 public tasks) and would clobber the prod-baked count to 0 on
    // first interaction. The count chip stays baked-fresh per deploy.
    publicApi
      .getPublicFeed(100)
      .then((feed) => {
        if (cancelled || !Array.isArray(feed)) return;
        // Narrow the merge to only the curated taskIds. The feed can
        // contain unrelated public executions; filtering here means the
        // skip-set guard below reflects the actual "did anything we
        // care about refresh?" question.
        const latestByTask = new Map<string, FeedExecutionLike>();
        for (const exec of feed as unknown as FeedExecutionLike[]) {
          if (!exec?.task_id || exec.status !== 'success') continue;
          if (!CONFIG_BY_ID.has(exec.task_id)) continue;
          const prior = latestByTask.get(exec.task_id);
          if (!prior || new Date(exec.started_at || 0) > new Date(prior.started_at || 0)) {
            latestByTask.set(exec.task_id, exec);
          }
        }
        // Skip the setState if no curated taskId got a live execution —
        // avoids an identity-change re-render that re-arms Hero's cycle
        // effect for nothing.
        if (latestByTask.size === 0) return;
        setSnapshot((prev) => ({
          ...prev,
          examples: prev.examples.map((entry) => {
            const exec = latestByTask.get(entry.taskId);
            return exec ? mergeExecution(entry, exec) : entry;
          }),
        }));
      })
      .catch(() => {
        // Swallow: snapshot stays as the build-time fallback. The
        // marketing route must never throw or render an error state.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<LandingExamplesContextValue>(() => {
    const { hero, cases } = partition(snapshot);
    return { snapshot, hero, cases };
  }, [snapshot]);

  return <LandingExamplesContext.Provider value={value}>{children}</LandingExamplesContext.Provider>;
}

export function useLandingExamples(): LandingExamplesContextValue {
  const ctx = useContext(LandingExamplesContext);
  if (!ctx) {
    // Defensive: components rendered outside the provider get the baked
    // snapshot directly so first paint is still meaningful (e.g. for
    // tests that render Hero in isolation).
    const { hero, cases } = partition(FALLBACK);
    return { snapshot: FALLBACK, hero, cases };
  }
  return ctx;
}
