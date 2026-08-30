import type { Metadata } from 'next'
import Link from 'next/link'
import { publicWatchPath } from '@/lib/watchRoutes'
import ReactMarkdown from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'

import {
  fetchPublicFeed,
  type PublicFeedExecution,
  type PublicGroundingSource,
} from '../../../lib/api/public'
import { formatTimeAgo } from '@/lib/utils'
import styles from '@/components/explore/Explore.module.css'
import { SCHEMA_CONTEXT } from '../../../lib/seo/jsonLd'
import { JsonLd } from '../../../lib/seo/jsonLdComponent'
import { makeConstrainedMarkdown } from '../../../lib/seo/constrainedMarkdown'

/**
 * /explore — public feed of recent triggered moments across all public
 * watches. Statically generated, revalidated every 5 minutes via ISR.
 */
export const revalidate = 300

export const metadata: Metadata = {
  // Root layout template (`%s · webwhen`) appends the brand suffix.
  title: 'Explore',
  description:
    'See what people are watching with webwhen — public watches and recent triggers across the open web.',
  alternates: {
    canonical: '/explore',
  },
  openGraph: {
    title: 'Explore — webwhen',
    description:
      'Public watches and recent triggers across the open web.',
    url: '/explore',
    type: 'website',
  },
}

// Constrained markdown map — same rules as MomentBlock. Inline `<a>` is
// rendered as inert text so the dashed sources row underneath owns linking.
const markdownCompact = makeConstrainedMarkdown({})

function getHost(url: string): string {
  try {
    return new URL(url).host.replace(/^www\./, '')
  } catch {
    return url
  }
}

function FeedEntry({ execution }: { execution: PublicFeedExecution }) {
  const content =
    execution.notification || execution.result?.evidence || 'No content found.'
  const sources: PublicGroundingSource[] =
    execution.result?.sources && execution.result.sources.length > 0
      ? execution.result.sources
      : execution.grounding_sources ?? []
  const isLong = content.length > 600

  return (
    <Link
      href={publicWatchPath(execution.task_id)}
      className={styles.entry}
      aria-label={`Open watch ${execution.task_name}`}
    >
      <div className={styles.entryEyebrow}>
        <span className={styles.entryEyebrowName}>{execution.task_name}</span>
        <span className={styles.entryEyebrowSep}>·</span>
        <span className={styles.entryEyebrowTime}>
          {formatTimeAgo(execution.started_at)}
        </span>
      </div>

      <div className={styles.entryBodyWrap}>
        <div
          className={`${styles.entryBody} ${isLong ? styles.entryClipped : ''}`}
        >
          <ReactMarkdown rehypePlugins={[rehypeSanitize]} components={markdownCompact}>
            {content}
          </ReactMarkdown>
        </div>
        {isLong && <div className={styles.entryFade} aria-hidden="true" />}
      </div>

      {sources.length > 0 && (
        <div className={styles.entrySources}>
          {sources.slice(0, 4).map((src, i) => (
            <div key={`${src.url}-${i}`} className={styles.entrySource}>
              <span className={styles.entrySourceHost}>{getHost(src.url)}</span>
              <span className={styles.entrySourceLink}>{src.title || src.url}</span>
            </div>
          ))}
        </div>
      )}
    </Link>
  )
}

export default async function ExplorePage() {
  const feed = await fetchPublicFeed({ limit: 50, revalidate: 300 })

  // schema.org ItemList for the feed — gives Googlebot structured access to
  // each triggered moment as a list item, with the per-task URL as `url`.
  const itemListJsonLd = {
    '@context': SCHEMA_CONTEXT,
    '@type': 'ItemList',
    name: 'webwhen — public watches feed',
    description:
      'Recent triggered moments from public webwhen watches across the open web.',
    itemListElement: feed.slice(0, 20).map((ex, idx) => ({
      '@type': 'ListItem',
      position: idx + 1,
      url: publicWatchPath(ex.task_id),
      name: ex.task_name,
    })),
  }

  return (
    <>
      {/* task_name is user-controlled; JsonLd escapes for inline-script safety. */}
      <JsonLd data={itemListJsonLd} />
      <div className={styles.column}>
        {feed.length === 0 ? (
          <div className={styles.empty}>
            <p className={styles.emptyPull}>Nothing public yet.</p>
            <p className={styles.emptySub}>
              Recent triggers from public watches will appear here.
            </p>
          </div>
        ) : (
          <div className={styles.feed}>
            {feed.map((execution) => (
              <FeedEntry key={execution.id} execution={execution} />
            ))}
          </div>
        )}
      </div>
    </>
  )
}
