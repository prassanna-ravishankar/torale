import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { MarketingLayout } from '../../_components/MarketingLayout'
import { breadcrumbJsonLd } from '../../_components/breadcrumbJsonLd'
import { cn } from '@/lib/utils'
import landingStyles from '@/components/landing/Landing.module.css'
import marketingStyles from '@/components/marketing/marketing.module.css'
import { COMPETITORS } from '@/data/competitors'
import { siteUrl } from '../../../../lib/api/origin'

interface PageProps {
  params: Promise<{ tool: string }>
}

export function generateStaticParams() {
  return Object.keys(COMPETITORS).map((tool) => ({ tool }))
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { tool } = await params
  const competitor = COMPETITORS[tool]
  if (!competitor) return { title: 'Not found', robots: { index: false } }
  return {
    title: competitor.seoTitle,
    description: competitor.seoDescription,
    alternates: { canonical: `/compare/${competitor.slug}` },
    openGraph: {
      type: 'article',
      url: siteUrl(`/compare/${competitor.slug}`),
      title: competitor.seoTitle,
      description: competitor.seoDescription,
      images: [siteUrl('/og-image.webp')],
    },
    twitter: {
      card: 'summary_large_image',
      title: competitor.seoTitle,
      description: competitor.seoDescription,
      images: [siteUrl('/og-image.webp')],
    },
  }
}

export default async function ComparePage({ params }: PageProps) {
  const { tool } = await params
  const competitor = COMPETITORS[tool]
  if (!competitor) notFound()

  const jsonLd = breadcrumbJsonLd([
    { name: 'Home', path: '/' },
    { name: 'Compare', path: '/compare' },
    { name: competitor.name, path: `/compare/${competitor.slug}` },
  ])

  return (
    <MarketingLayout activePath="/compare">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: jsonLd }}
      />

      <section className={cn(landingStyles.section, marketingStyles.articleHero)}>
        <div className={landingStyles.container}>
          <div className={marketingStyles.reading}>
            <div className={marketingStyles.articleHeroEyebrow}>vs {competitor.name}</div>
            <h1 className={marketingStyles.articleHeading}>{competitor.heroHeadline}</h1>
            <p className={marketingStyles.articleLede}>{competitor.heroLede}</p>
          </div>
        </div>
      </section>

      <section className={landingStyles.section}>
        <div className={landingStyles.container}>
          <div className={marketingStyles.reading}>
            <p className={landingStyles.manifestoQuote}>{competitor.openingQuote}</p>
            {competitor.body.map((para, i) => (
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
          <div className={marketingStyles.reading}>
            <div className={landingStyles.eyebrow}>The honest difference</div>
            <p className={landingStyles.manifestoQuote} style={{ marginTop: '24px' }}>
              {competitor.differentiator}
            </p>
          </div>
        </div>
      </section>

      <section className={cn(landingStyles.section, landingStyles.cta)}>
        <div className={landingStyles.container}>
          <h2 className={landingStyles.ctaHeading}>
            Try webwhen <span className={landingStyles.heroEmber}>instead</span>.
          </h2>
          <p className={landingStyles.ctaBody}>
            Free while in beta. No setup, no configuration. The agent decides everything.
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
