import type { Metadata } from 'next'

import { MarketingLayout } from '../_components/MarketingLayout'
import { cn } from '@/lib/utils'
import landingStyles from '@/components/landing/Landing.module.css'
import marketingStyles from '@/components/marketing/marketing.module.css'
import type { ChangelogEntry } from '@/types/changelog'

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const CATEGORY_LABELS: Record<ChangelogEntry['category'], string> = {
  feature: 'new',
  improvement: 'improvement',
  fix: 'fix',
  infra: 'infrastructure',
  research: 'research',
}

export const metadata: Metadata = {
  title: 'Changelog — webwhen',
  description: 'What webwhen has been up to. Built in the open.',
  alternates: {
    canonical: '/changelog',
    types: {
      'application/rss+xml': `${SITE_ORIGIN}/changelog.xml`,
    },
  },
  openGraph: {
    type: 'website',
    url: `${SITE_ORIGIN}/changelog`,
    title: 'Changelog — webwhen',
    description: 'What webwhen has been up to. Built in the open.',
    images: [`${SITE_ORIGIN}/og-image.webp`],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Changelog — webwhen',
    description: 'What webwhen has been up to. Built in the open.',
    images: [`${SITE_ORIGIN}/og-image.webp`],
  },
}

// Fetched server-side with ISR (10min). Replaces the Vite-era
// __PRERENDER_CHANGELOG__ global + runtime refetch dance. The JSON-LD
// emitted below is the #261 postcondition — at least one TechArticle item
// must appear in the rendered HTML.
// Build-time filesystem fallback. The backend HTTP endpoint isn't reachable
// during `next build` in CI/sandbox shells, but the source JSON is checked
// in alongside the frontend at ../backend/static/changelog.json. Reading
// the file synchronously here means SSG always renders article-level
// JSON-LD (preserves the #261 postcondition); ISR replaces it on the first
// real request once the API is live.
async function fetchChangelog(): Promise<ChangelogEntry[]> {
  try {
    const res = await fetch(`${API_BASE}/static/changelog.json`, {
      next: { revalidate: 600 },
    })
    if (res.ok) {
      const data = (await res.json()) as ChangelogEntry[]
      if (Array.isArray(data) && data.length > 0) return data
    }
  } catch {
    // fall through to filesystem fallback
  }

  try {
    const { readFile } = await import('node:fs/promises')
    const path = await import('node:path')
    const fallbackPath = path.resolve(
      process.cwd(),
      '..',
      'backend',
      'static',
      'changelog.json',
    )
    const raw = await readFile(fallbackPath, 'utf-8')
    const data = JSON.parse(raw) as ChangelogEntry[]
    return Array.isArray(data) ? data : []
  } catch {
    return []
  }
}

function formatChangelogDate(dateStr: string): string {
  return new Date(`${dateStr}T00:00:00`).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function buildStructuredData(entries: ChangelogEntry[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'webwhen Changelog',
    description:
      'Product updates and releases for webwhen, the AI agent that watches the open web and tells you when something matters.',
    url: `${SITE_ORIGIN}/changelog`,
    publisher: {
      '@type': 'Organization',
      name: 'webwhen',
      url: SITE_ORIGIN,
      logo: {
        '@type': 'ImageObject',
        url: `${SITE_ORIGIN}/brand/webwhen-mark.svg`,
        width: 512,
        height: 512,
      },
      sameAs: ['https://github.com/prassanna-ravishankar/webwhen'],
    },
    mainEntity: {
      '@type': 'ItemList',
      numberOfItems: entries.length,
      itemListElement: entries.slice(0, 50).map((entry, idx) => ({
        '@type': 'ListItem',
        position: idx + 1,
        item: {
          '@type': 'TechArticle',
          headline: entry.title,
          datePublished: entry.date,
          dateModified: entry.date,
          articleSection: entry.category,
          description: entry.description,
          author: { '@type': 'Organization', name: 'webwhen' },
          publisher: { '@type': 'Organization', name: 'webwhen' },
        },
      })),
    },
    breadcrumb: {
      '@type': 'BreadcrumbList',
      itemListElement: [
        {
          '@type': 'ListItem',
          position: 1,
          name: 'Home',
          item: SITE_ORIGIN,
        },
        {
          '@type': 'ListItem',
          position: 2,
          name: 'Changelog',
          item: `${SITE_ORIGIN}/changelog`,
        },
      ],
    },
  }
}

export default async function ChangelogPage() {
  const entries = await fetchChangelog()
  const structuredJson = JSON.stringify(buildStructuredData(entries)).replace(
    /</g,
    '\\u003c',
  )

  return (
    <MarketingLayout activePath="/changelog">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: structuredJson }}
      />

      <section
        className={cn(landingStyles.section, marketingStyles.articleHero)}
      >
        <div className={landingStyles.container}>
          <div style={{ maxWidth: '720px', margin: '0 auto' }}>
            <div className={marketingStyles.articleHeroEyebrow}>Changelog</div>
            <h1 className={marketingStyles.articleHeading}>
              What webwhen has been{' '}
              <span className={marketingStyles.articleHeroEmber}>up to</span>.
            </h1>
            <p className={marketingStyles.articleLede}>
              Built in the open. New since you last looked.
            </p>
          </div>
        </div>
      </section>

      <section className={landingStyles.section} style={{ paddingTop: 0 }}>
        <div className={landingStyles.container}>
          <div style={{ maxWidth: '760px', margin: '0 auto' }}>
            {entries.length === 0 && (
              <p className={marketingStyles.stamp}>No entries yet.</p>
            )}

            <div className={marketingStyles.feed}>
              {entries.map((entry) => {
                const tagLabel = CATEGORY_LABELS[entry.category]
                const highlight = entry.category === 'feature'
                const formattedDate = formatChangelogDate(entry.date)

                return (
                  <article
                    key={entry.id}
                    className={marketingStyles.feedEntry}
                  >
                    <div className={marketingStyles.feedEntryDate}>
                      {formattedDate}
                    </div>
                    <div className={marketingStyles.feedEntryBody}>
                      {tagLabel && (
                        <div
                          className={cn(
                            marketingStyles.feedEntryTag,
                            highlight && marketingStyles.feedEntryTagEmber,
                          )}
                        >
                          {tagLabel}
                        </div>
                      )}
                      <h2>{entry.title}</h2>
                      {entry.description && <p>{entry.description}</p>}
                    </div>
                  </article>
                )
              })}
            </div>
          </div>
        </div>
      </section>
    </MarketingLayout>
  )
}
