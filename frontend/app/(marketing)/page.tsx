import type { Metadata } from 'next'

import { MarketingLayout } from './_components/MarketingLayout'
import { Hero } from './_components/landing/Hero'
import { Steps } from './_components/landing/Steps'
import { Cases } from './_components/landing/Cases'
import { Manifesto } from './_components/landing/Manifesto'
import { CTA } from './_components/landing/CTA'
import { LandingExamplesProvider } from './_components/landing/LandingExamplesContext'
import { jsonLdHtml } from '../../lib/seo/jsonLd'

const SITE_ORIGIN =
  process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai'

// Per publicRoutes.ts: /, priority 1.0.
export const metadata: Metadata = {
  title: 'webwhen — the agent that waits for the web',
  description:
    'Tell webwhen what to watch for in plain English. It will sit with the question, search the web on a schedule, and tell you the moment your condition is met.',
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    url: `${SITE_ORIGIN}/`,
    title: 'webwhen — the agent that waits for the web',
    description:
      'Tell webwhen what to watch for in plain English. It will sit with the question, search the web on a schedule, and tell you the moment your condition is met.',
    images: [`${SITE_ORIGIN}/og-image.webp`],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'webwhen — the agent that waits for the web',
    description:
      'Tell webwhen what to watch for in plain English. It will sit with the question, search the web on a schedule, and tell you the moment your condition is met.',
    images: [`${SITE_ORIGIN}/og-image.webp`],
  },
}

// SoftwareApplication JSON-LD — preserved verbatim from src/components/Landing.tsx.
const softwareJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'webwhen',
  applicationCategory: 'WebApplication',
  operatingSystem: 'Web',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD',
  },
  description:
    'Tell webwhen what to watch for in plain English. It searches the web on a schedule and tells you the moment your condition is met.',
}

export default function LandingPage() {
  return (
    <MarketingLayout activePath="">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: jsonLdHtml(softwareJsonLd) }}
      />
      <LandingExamplesProvider>
        <Hero />
        <Steps />
        <Cases />
        <Manifesto />
        <CTA />
      </LandingExamplesProvider>
    </MarketingLayout>
  )
}
