import type { MetadataRoute } from 'next'
import { publicWatchPath } from '@/lib/watchRoutes'
import { PUBLIC_ROUTES } from '../lib/publicRoutes'
import { fetchPublicTasksList } from '../lib/api/public'
import { siteUrl } from '../lib/api/origin'

// Single source-of-truth sitemap, served at /sitemap.xml. Replaces the
// previous split between backend's /sitemap.xml (index) + /sitemap-dynamic.xml
// (DB-derived) and frontend's /sitemap-static.xml (enumerated routes). Next's
// framework convention emits XML, content-type, and ETag for us; ISR handles
// freshness via `revalidate` below.

export const revalidate = 86400

// Public-tasks endpoint caps `limit` at 100 (server-side Pydantic validation).
// At current scale the public-task count is well under that; if it grows past
// 100, split into a sitemap-index with paged children (Next supports paged
// sitemaps via the `id` segment in `app/sitemap/[id]/sitemap.ts`).
const PUBLIC_TASK_LIMIT = 100

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const lastModified = new Date()

  const enumerated: MetadataRoute.Sitemap = PUBLIC_ROUTES.map((route) => ({
    url: siteUrl(route.path),
    lastModified,
    priority: route.priority ?? 0.8,
  }))

  // /explore aggregates recent triggered watches; ISR-revalidated every 5m
  // on the page itself, so daily lastmod is the right Google hint.
  enumerated.push({
    url: siteUrl('/explore'),
    lastModified,
    priority: 0.8,
  })

  // Top-N public tasks. Falls back to [] if the backend is unreachable so a
  // CI build never breaks; ISR will fill in once the API comes up.
  const tasks = await fetchPublicTasksList({ limit: PUBLIC_TASK_LIMIT }).catch(
    () => [],
  )
  for (const task of tasks) {
    enumerated.push({
      url: siteUrl(publicWatchPath(task.id)),
      lastModified: task.updated_at ? new Date(task.updated_at) : lastModified,
      priority: 0.6,
    })
  }

  return enumerated
}
