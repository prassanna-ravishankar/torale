import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'

import {
  fetchPublicTaskById,
  fetchPublicTasksList,
  isUuid,
  type PublicGroundingSource,
  type PublicTask,
} from '../../../../lib/api/public'
import { apiUrl, getSiteOrigin } from '../../../../lib/api/origin'
import { formatTimeAgo } from '@/lib/utils'
import watchStyles from '@/components/watch/Watch.module.css'
import { SCHEMA_CONTEXT } from '../../../../lib/seo/jsonLd'
import { JsonLd } from '../../../../lib/seo/jsonLdComponent'
import { makeConstrainedMarkdown } from '../../../../lib/seo/constrainedMarkdown'

/** Public, statically-rendered watch detail page; private tasks 404. */
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
const momentMarkdown = makeConstrainedMarkdown({
  paragraph: watchStyles.momentAnswerP,
  list: watchStyles.momentList,
  listItem: watchStyles.momentListItem,
})

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
    '@context': SCHEMA_CONTEXT,
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

  const siteOrigin = getSiteOrigin()

  return (
    <>
      <JsonLd data={buildJsonLd(task, siteOrigin)} />
      <link
        rel="alternate"
        type="application/rss+xml"
        title={`${task.name || 'watch'} — RSS feed`}
        href={apiUrl(`/tasks/${task.id}/rss`)}
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
            {/* Passive affordance — statically rendered for everyone.
                Signed-in owners click through to the dashboard view;
                visitors without a Clerk session land on /sign-in. Avoids
                conditional rendering so the page stays cacheable. */}
            <span>
              <Link href={`/dashboard/tasks/${task.id}`}>open in dashboard →</Link>
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
