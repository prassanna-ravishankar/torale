import type { Metadata } from 'next'
import Link from 'next/link'
import ReactMarkdown, { type Components } from 'react-markdown'
import rehypeSanitize from 'rehype-sanitize'

import {
  fetchPublicFeed,
  type PublicFeedExecution,
  type PublicGroundingSource,
} from '../../../lib/api/public'
import { formatTimeAgo } from '@/lib/utils'
import styles from '@/components/explore/Explore.module.css'
import { jsonLdHtml } from '../../../lib/seo/jsonLd'

/**
 * /explore — public feed of recent triggered moments across all public
 * watches. Statically generated at build time, revalidated every 5 minutes
 * via ISR so crawlers and human visitors get pre-rendered HTML with real
 * content (the whole point of issue #334 / the Next.js migration).
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

// Constrained markdown map — same rules as src/components/watch/MomentBlock
// and src/route-views/Explore. Inline `<a>` is rendered as inert text so the
// dashed sources row underneath owns linking.
const markdownCompact: Components = {
  p: ({ children }) => <p>{children}</p>,
  strong: ({ children }) => <strong>{children}</strong>,
  em: ({ children }) => <em>{children}</em>,
  ul: ({ children }) => <ul>{children}</ul>,
  ol: ({ children }) => <ol>{children}</ol>,
  li: ({ children }) => <li>{children}</li>,
  h1: ({ children }) => <p>{children}</p>,
  h2: ({ children }) => <p>{children}</p>,
  h3: ({ children }) => <p>{children}</p>,
  h4: ({ children }) => <p>{children}</p>,
  h5: ({ children }) => <p>{children}</p>,
  h6: ({ children }) => <p>{children}</p>,
  code: ({ children }) => <span>{children}</span>,
  pre: ({ children }) => <p>{children}</p>,
  img: () => null,
  a: ({ children }) => <span>{children}</span>,
}

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
      href={`/tasks/${execution.task_id}`}
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
    '@context': 'https://schema.org',
    '@type': 'ItemList',
    name: 'webwhen — public watches feed',
    description:
      'Recent triggered moments from public webwhen watches across the open web.',
    itemListElement: feed.slice(0, 20).map((ex, idx) => ({
      '@type': 'ListItem',
      position: idx + 1,
      url: `/tasks/${ex.task_id}`,
      name: ex.task_name,
    })),
  }

  return (
    <>
      <script
        type="application/ld+json"
        // task_name is user-controlled; jsonLdHtml() escapes for inline-script safety.
        dangerouslySetInnerHTML={{ __html: jsonLdHtml(itemListJsonLd) }}
      />
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
