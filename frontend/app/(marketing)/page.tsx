import type { Metadata } from 'next'

import { MarketingLayout } from './_components/MarketingLayout'
import { Hero } from './_components/landing/Hero'
import { Steps } from './_components/landing/Steps'
import { Cases } from './_components/landing/Cases'
import { Manifesto } from './_components/landing/Manifesto'
import { CTA } from './_components/landing/CTA'
import { LandingExamplesProvider } from './_components/landing/LandingExamplesContext'
import { SCHEMA_CONTEXT } from '../../lib/seo/jsonLd'
import { JsonLd } from '../../lib/seo/jsonLdComponent'
import { siteUrl } from '../../lib/api/origin'

// Per lib/publicRoutes.ts: /, priority 1.0.
export const metadata: Metadata = {
  title: 'webwhen — the agent that waits for the web',
  description:
    'Tell webwhen what to watch for in plain English. It will sit with the question, search the web on a schedule, and tell you the moment your condition is met.',
  alternates: { canonical: '/' },
  openGraph: {
    type: 'website',
    url: siteUrl('/'),
    title: 'webwhen — the agent that waits for the web',
    description:
      'Tell webwhen what to watch for in plain English. It will sit with the question, search the web on a schedule, and tell you the moment your condition is met.',
    images: [siteUrl('/og-image.webp')],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'webwhen — the agent that waits for the web',
    description:
      'Tell webwhen what to watch for in plain English. It will sit with the question, search the web on a schedule, and tell you the moment your condition is met.',
    images: [siteUrl('/og-image.webp')],
  },
}

const softwareJsonLd = {
  '@context': SCHEMA_CONTEXT,
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
      <JsonLd data={softwareJsonLd} />
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
