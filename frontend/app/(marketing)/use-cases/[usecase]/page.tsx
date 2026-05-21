import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { MarketingLayout } from '../../_components/MarketingLayout'
import { breadcrumbJsonLd } from '../../_components/breadcrumbJsonLd'
import { cn } from '@/lib/utils'
import landingStyles from '@/components/landing/Landing.module.css'
import marketingStyles from '@/components/marketing/marketing.module.css'
import { USE_CASES } from '@/data/useCases'

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

interface PageProps {
  params: Promise<{ usecase: string }>
}

export function generateStaticParams() {
  return Object.keys(USE_CASES).map((usecase) => ({ usecase }))
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { usecase } = await params
  const data = USE_CASES[usecase]
  if (!data) return { title: 'Not found', robots: { index: false } }
  const title = data.seoTitle ?? `${data.heroHeadline} — webwhen`
  const description = data.seoDescription ?? data.heroLede
  return {
    title,
    description,
    alternates: { canonical: `/use-cases/${data.slug}` },
    openGraph: {
      type: 'article',
      url: `${SITE_ORIGIN}/use-cases/${data.slug}`,
      title,
      description,
      images: [`${SITE_ORIGIN}/og-image.webp`],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [`${SITE_ORIGIN}/og-image.webp`],
    },
  }
}

export default async function UseCasePage({ params }: PageProps) {
  const { usecase } = await params
  const data = USE_CASES[usecase]
  if (!data) notFound()

  const others = Object.values(USE_CASES).filter((u) => u.slug !== data.slug)

  const jsonLd = breadcrumbJsonLd([
    { name: 'Home', path: '/' },
    { name: 'Use cases', path: '/use-cases' },
    { name: data.name, path: `/use-cases/${data.slug}` },
  ])

  return (
    <MarketingLayout activePath="/use-cases">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: jsonLd }}
      />

      <section className={cn(landingStyles.section, marketingStyles.articleHero)}>
        <div className={landingStyles.container}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1.1fr 0.9fr',
              gap: '80px',
              alignItems: 'center',
            }}
          >
            <div>
              <div className={marketingStyles.articleHeroEyebrow}>Use case</div>
              <h1 className={marketingStyles.articleHeading}>{data.heroHeadline}</h1>
              <p className={marketingStyles.articleLede}>{data.heroLede}</p>
            </div>
            <div className={landingStyles.composer}>
              <div className={landingStyles.composerHead}>
                <span>new watch</span>
                <span>plain english · no rules</span>
              </div>
              <div className={landingStyles.composerBody}>
                <p className={landingStyles.composerPrompt}>
                  {data.composerPrompt}
                  <span className={landingStyles.composerCursor}></span>
                </p>
                <p className={landingStyles.composerSub}>
                  webwhen will sit with this and decide when to check.
                </p>
              </div>
              <div className={landingStyles.composerFoot}>
                <div>
                  <span className={landingStyles.chip}>nothing to tune</span>
                </div>
                <Link
                  href="/sign-up"
                  className={cn(landingStyles.btn, landingStyles.btnPrimary)}
                  style={{ padding: '8px 14px' }}
                >
                  Watch{' '}
                  <span style={{ fontFamily: 'var(--ww-font-mono)' }}>→</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className={landingStyles.section}>
        <div className={landingStyles.container}>
          <div className={marketingStyles.reading}>
            <p className={landingStyles.manifestoQuote}>{data.openingQuote}</p>
            {data.body.map((para, i) => (
              <p
                key={i}
                className={landingStyles.manifestoBody}
                style={i === 0 ? { marginTop: '32px' } : undefined}
              >
                {para}
              </p>
            ))}
          </div>
        </div>
      </section>

      <section className={cn(landingStyles.section, landingStyles.sectionAlt)}>
        <div className={landingStyles.container}>
          <div className={landingStyles.eyebrow}>Other watches</div>
          <h2 className={landingStyles.sectionHeading}>
            Things webwhen also{' '}
            <span className={landingStyles.sectionHeadingAccent}>waits for.</span>
          </h2>
          <div className={landingStyles.cases}>
            {others.map((u) => (
              <Link
                key={u.slug}
                href={`/use-cases/${u.slug}`}
                className={landingStyles.caseCard}
              >
                <div className={landingStyles.caseTag}>{u.shortTag}</div>
                <p className={landingStyles.caseQuestion}>{u.composerPrompt}</p>
                <div className={landingStyles.caseResult}>watching</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className={cn(landingStyles.section, landingStyles.cta)}>
        <div className={landingStyles.container}>
          <h2 className={landingStyles.ctaHeading}>
            What are you waiting{' '}
            <span className={landingStyles.heroEmber}>for</span>?
          </h2>
          <p className={landingStyles.ctaBody}>
            Free while in beta. One condition takes about 30 seconds to set up.
          </p>
          <Link
            href="/sign-up"
            className={cn(landingStyles.btn, landingStyles.btnPrimary, landingStyles.btnLg)}
          >
            Start watching{' '}
            <span style={{ fontFamily: 'var(--ww-font-mono)' }}>→</span>
          </Link>
        </div>
      </section>
    </MarketingLayout>
  )
}
