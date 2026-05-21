import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import ReactMarkdown, { type Components } from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'

import {
  fetchPublicTaskById,
  fetchPublicTasksList,
  isUuid,
  type PublicGroundingSource,
  type PublicTask,
} from '../../../../lib/api/public'
import { formatTimeAgo } from '@/lib/utils'
import watchStyles from '@/components/watch/Watch.module.css'

/**
 * /tasks/[taskId] — public, statically-rendered watch detail page.
 *
 * The whole point of issue #334 / the Next.js migration: Googlebot now
 * receives real HTML containing the watch's condition and its most recent
 * triggered moment, instead of an empty SPA shell. Private tasks 404 (we
 * never even include them in `generateStaticParams`, so they cannot be
 * cached at the CDN edge).
 *
 * Authenticated viewing (owner actions: run, pause, edit, delete) stays on
 * the in-app dashboard route group. This static page intentionally renders
 * the anonymous view only — layering an authed enhancement on top is a
 * follow-up (see report).
 */
export const revalidate = 60
export const dynamicParams = true

/** Pre-render the top-N most popular public tasks at build time. */
export async function generateStaticParams() {
  const tasks = await fetchPublicTasksList({ limit: 100 })
  return tasks.map((t) => ({ taskId: t.id }))
}

/** Per-task `<title>` / OpenGraph / canonical — load-bearing for SEO. */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ taskId: string }>
}): Promise<Metadata> {
  const { taskId } = await params
  if (!isUuid(taskId)) {
    return { title: 'Watch not found' }
  }
  const task = await fetchPublicTaskById(taskId)
  if (!task) {
    return { title: 'Watch not found' }
  }
  // Headline: prefer the human name, fall back to the condition (which the
  // agent stores as the original "tell me when …" prompt). The root layout
  // template (`%s · webwhen`) appends the brand suffix automatically.
  const title = task.name || task.condition_description
  const description = task.condition_description
  const canonical = `/tasks/${task.id}`
  return {
    title,
    description,
    alternates: { canonical },
    openGraph: {
      title,
      description,
      url: canonical,
      type: 'article',
    },
  }
}

// Constrained markdown — same allowlist as MomentBlock / Explore.
const momentMarkdown: Components = {
  p: ({ children }) => <p className={watchStyles.momentAnswerP}>{children}</p>,
  strong: ({ children }) => <strong>{children}</strong>,
  em: ({ children }) => <em>{children}</em>,
  ul: ({ children }) => <ul className={watchStyles.momentList}>{children}</ul>,
  ol: ({ children }) => <ol className={watchStyles.momentList}>{children}</ol>,
  li: ({ children }) => <li className={watchStyles.momentListItem}>{children}</li>,
  h1: ({ children }) => <p className={watchStyles.momentAnswerP}>{children}</p>,
  h2: ({ children }) => <p className={watchStyles.momentAnswerP}>{children}</p>,
  h3: ({ children }) => <p className={watchStyles.momentAnswerP}>{children}</p>,
  h4: ({ children }) => <p className={watchStyles.momentAnswerP}>{children}</p>,
  h5: ({ children }) => <p className={watchStyles.momentAnswerP}>{children}</p>,
  h6: ({ children }) => <p className={watchStyles.momentAnswerP}>{children}</p>,
  code: ({ children }) => <span>{children}</span>,
  pre: ({ children }) => <p className={watchStyles.momentAnswerP}>{children}</p>,
  img: () => null,
  a: ({ children }) => <span>{children}</span>,
}

function hostFromUrl(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function MomentBlock({
  notification,
  evidence,
  sources,
  completedAt,
  startedAt,
}: {
  notification: string | null
  evidence: string | undefined
  sources: PublicGroundingSource[]
  completedAt: string | null
  startedAt: string
}) {
  const answer = notification || evidence || ''
  const when = formatTimeAgo(completedAt || startedAt)
  return (
    <article className={watchStyles.moment}>
      <div className={watchStyles.momentWhen}>
        <span>the moment · {when}</span>
      </div>
      {answer ? (
        <div className={watchStyles.momentAnswer}>
          <ReactMarkdown rehypePlugins={[rehypeSanitize]} components={momentMarkdown}>
            {answer}
          </ReactMarkdown>
        </div>
      ) : null}
      {sources.length > 0 && (
        <div className={watchStyles.momentSources}>
          {sources.map((s, i) => {
            const host = hostFromUrl(s.url)
            const label = s.title || s.url
            return (
              <div key={`${s.url}-${i}`} className={watchStyles.momentSrc}>
                <span className={watchStyles.momentSrcHost}>{host}</span>
                <a
                  className={watchStyles.momentSrcLink}
                  href={s.url}
                  target="_blank"
                  rel="noreferrer noopener nofollow"
                  title={label}
                >
                  {label}
                </a>
              </div>
            )
          })}
        </div>
      )}
    </article>
  )
}

function buildJsonLd(task: PublicTask, origin: string) {
  const last = task.last_execution
  const articleBody =
    last?.notification ||
    last?.result?.notification ||
    last?.result?.evidence ||
    task.condition_description
  const datePublished = task.created_at
  const dateModified =
    last?.completed_at || last?.started_at || task.updated_at || task.created_at
  return {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: task.name || task.condition_description,
    description: task.condition_description,
    articleBody,
    datePublished,
    dateModified,
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `${origin}/tasks/${task.id}`,
    },
    author: { '@type': 'Organization', name: 'webwhen' },
    publisher: { '@type': 'Organization', name: 'webwhen' },
  }
}

export default async function PublicTaskPage({
  params,
}: {
  params: Promise<{ taskId: string }>
}) {
  const { taskId } = await params
  if (!isUuid(taskId)) notFound()

  const task = await fetchPublicTaskById(taskId)
  if (!task) notFound()

  const last = task.last_execution
  const sources: PublicGroundingSource[] =
    last?.result?.sources && last.result.sources.length > 0
      ? last.result.sources
      : last?.grounding_sources ?? []

  const lastWhen = last?.completed_at || last?.started_at || null

  const siteOrigin =
    process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(buildJsonLd(task, siteOrigin)),
        }}
      />
      <link
        rel="alternate"
        type="application/rss+xml"
        title={`${task.name || 'watch'} — RSS feed`}
        href={`${process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.webwhen.ai'}/tasks/${task.id}/rss`}
      />

      <header className={watchStyles.detailHead}>
        <div className={watchStyles.left}>
          <div className={watchStyles.pillRow}>
            <span
              className={`${watchStyles.pill} ${
                last?.notification ? watchStyles.pillTriggered : watchStyles.pillWatching
              }`}
            >
              {last?.notification ? 'triggered' : 'watching'}
            </span>
          </div>
          <h1 className={watchStyles.question}>{task.condition_description}</h1>
          <div className={watchStyles.meta}>
            {lastWhen && (
              <span>
                <strong>checked</strong> {formatTimeAgo(lastWhen)}
              </span>
            )}
            <span>
              <strong>views</strong> {task.view_count}
            </span>
            <span>
              <Link href="/explore">← back to explore</Link>
            </span>
          </div>
        </div>
      </header>

      {last && (last.notification || last.result?.evidence) ? (
        <>
          <h2 className={watchStyles.sectionH}>the moment</h2>
          <MomentBlock
            notification={last.notification}
            evidence={last.result?.evidence}
            sources={sources}
            completedAt={last.completed_at}
            startedAt={last.started_at}
          />
        </>
      ) : (
        <p className={watchStyles.momentAnswer}>
          webwhen is sitting with this question. Check back soon.
        </p>
      )}
    </>
  )
}
