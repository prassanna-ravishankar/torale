/**
 * Server-side wrappers for the public (NO AUTH) backend endpoints used by
 * statically-rendered marketing routes:
 *
 *  - GET /api/v1/public/feed                  → recent triggered moments
 *  - GET /api/v1/public/tasks?sort_by=recent  → list public tasks
 *  - GET /api/v1/public/tasks/id/{uuid}       → one public task
 *
 * Shapes mirror backend Pydantic models in
 *   backend/src/webwhen/api/routers/public_tasks.py
 * and the existing FE types in frontend/src/types/index.ts. We re-declare a
 * small subset here so RSC code never reaches into `@/types` (which is wired
 * for the Vite tree). Keep this surface narrow on purpose.
 */
import { apiUrl } from './origin'

// ---------- Shared shapes -------------------------------------------------

export interface PublicGroundingSource {
  url: string
  title?: string
}

export interface PublicExecutionResult {
  evidence?: string
  notification?: string
  sources?: PublicGroundingSource[]
  confidence?: number
}

export interface PublicFeedExecution {
  id: string
  task_id: string
  task_name: string
  task_search_query: string | null
  task_is_public: boolean
  status: string
  started_at: string
  completed_at: string | null
  notification: string | null
  result: PublicExecutionResult | null
  grounding_sources: PublicGroundingSource[]
}

export interface PublicTask {
  id: string
  name: string
  search_query: string
  condition_description: string
  state: 'active' | 'paused' | 'completed'
  created_at: string
  updated_at: string | null
  next_run: string | null
  is_public: boolean
  view_count: number
  subscriber_count: number
  last_execution: {
    id: string
    notification: string | null
    started_at: string
    completed_at: string | null
    status: string
    result: PublicExecutionResult | null
    grounding_sources: PublicGroundingSource[] | null
  } | null
}

interface PublicTasksListResponse {
  tasks: PublicTask[]
  total: number
  offset: number
  limit: number
}

// ---------- UUID validation ----------------------------------------------

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export function isUuid(value: string): boolean {
  return UUID_RE.test(value)
}

// ---------- Fetchers ------------------------------------------------------

/**
 * Fetch the global public feed. Returns `[]` on any non-2xx — feed pages
 * should never explode if the backend is briefly unreachable; ISR will
 * refresh on the next revalidate tick.
 */
export async function fetchPublicFeed(
  options: { limit?: number; revalidate?: number } = {},
): Promise<PublicFeedExecution[]> {
  const limit = options.limit ?? 50
  const revalidate = options.revalidate ?? 300
  const url = apiUrl(`/api/v1/public/feed?limit=${limit}`)
  try {
    const res = await fetch(url, { next: { revalidate } })
    if (!res.ok) {
      console.warn(`[public api] feed ${res.status} from ${url}`)
      return []
    }
    return (await res.json()) as PublicFeedExecution[]
  } catch (err) {
    console.warn(`[public api] feed fetch failed: ${(err as Error).message}`)
    return []
  }
}

/**
 * Fetch a paged list of public tasks. Used by `generateStaticParams` to
 * decide which task pages to prerender at build time. Returns `[]` on any
 * failure so the build keeps going; `dynamicParams: true` will render the
 * rest on-demand.
 */
export async function fetchPublicTasksList(
  options: { limit?: number; offset?: number; revalidate?: number } = {},
): Promise<PublicTask[]> {
  const limit = options.limit ?? 100
  const offset = options.offset ?? 0
  const revalidate = options.revalidate ?? 3600
  const url = apiUrl(
    `/api/v1/public/tasks?limit=${limit}&offset=${offset}&sort_by=popular`,
  )
  try {
    const res = await fetch(url, { next: { revalidate } })
    if (!res.ok) {
      console.warn(`[public api] tasks list ${res.status} from ${url}`)
      return []
    }
    const body = (await res.json()) as PublicTasksListResponse
    return body.tasks ?? []
  } catch (err) {
    console.warn(`[public api] tasks list fetch failed: ${(err as Error).message}`)
    return []
  }
}

/**
 * Fetch one public task by UUID. Returns `null` on 404 or any non-2xx —
 * the page should `notFound()` so Next emits the correct 404 status (which
 * matters for SEO: private/missing tasks must not surface in search).
 */
export async function fetchPublicTaskById(
  taskId: string,
  options: { revalidate?: number } = {},
): Promise<PublicTask | null> {
  if (!isUuid(taskId)) return null
  const revalidate = options.revalidate ?? 60
  const url = apiUrl(`/api/v1/public/tasks/id/${taskId}`)
  try {
    const res = await fetch(url, { next: { revalidate } })
    if (!res.ok) {
      if (res.status !== 404) {
        console.warn(`[public api] task ${taskId} → ${res.status}`)
      }
      return null
    }
    const task = (await res.json()) as PublicTask
    // Defense-in-depth: backend should already filter to public tasks at
    // this endpoint for anonymous viewers, but never render a non-public
    // task statically — that would leak user content into a CDN cache.
    if (!task.is_public) return null
    return task
  } catch (err) {
    console.warn(`[public api] task ${taskId} fetch failed: ${(err as Error).message}`)
    return null
  }
}
