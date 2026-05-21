import type { Metadata } from 'next'

import { MarketingLayout } from '../_components/MarketingLayout'
import { cn } from '@/lib/utils'
import landingStyles from '@/components/landing/Landing.module.css'
import marketingStyles from '@/components/marketing/marketing.module.css'
import type { ChangelogEntry } from '@/types/changelog'
import { apiUrl, getSiteOrigin } from '../../../lib/api/origin'
import { SCHEMA_CONTEXT } from '../../../lib/seo/jsonLd'
import { JsonLd } from '../../../lib/seo/jsonLdComponent'

const SITE_ORIGIN = getSiteOrigin()

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

// Fetched server-side with ISR (10min). The emitted JSON-LD is the #261
// postcondition — at least one TechArticle item must appear in the
// rendered HTML; the filesystem fallback below preserves that invariant
// when the backend HTTP endpoint isn't reachable during `next build`.
async function fetchChangelog(): Promise<ChangelogEntry[]> {
  try {
    const res = await fetch(apiUrl('/static/changelog.json'), {
      next: { revalidate: 600 },
    })
    if (res.ok) {
      const data = (await res.json()) as ChangelogEntry[]
      if (Array.isArray(data) && data.length > 0) return data
    }
  } catch {
    // fall through to filesystem fallback
  }

  // Build-time fallback: scripts/sync-changelog-fixture.mjs (prebuild) copies
  // backend/static/changelog.json into frontend/.changelog-fixture.json before
  // `next build`. Resolving relative to ../backend/ doesn't work in the Docker
  // builder stage because the frontend image's build context is `frontend/`
  // alone — `../backend/` is outside the context.
  try {
    const { readFile } = await import('node:fs/promises')
    const path = await import('node:path')
    const fallbackPath = path.resolve(process.cwd(), '.changelog-fixture.json')
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
    '@context': SCHEMA_CONTEXT,
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

  return (
    <MarketingLayout activePath="/changelog">
      <JsonLd data={buildStructuredData(entries)} />

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
