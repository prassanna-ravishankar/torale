import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import './globals.css'
import { OrganizationJsonLd } from '../components/seo/OrganizationJsonLd'
import { PostHogProvider } from '../components/analytics/PostHogProvider'
import { getSiteOrigin } from '../lib/api/origin'

// Root metadata — per-page metadata in (marketing)/* and (app)/* overrides
// title via `template`. See app/(marketing)/page.tsx etc.
export const metadata: Metadata = {
  title: {
    default: 'webwhen — the agent that waits for the web',
    template: '%s · webwhen',
  },
  description:
    'Tell webwhen what to watch for in plain English. It will sit with the question, search the web on a schedule, and tell you the moment your condition is met.',
  metadataBase: new URL(getSiteOrigin()),
}

// Root layout intentionally does NOT mount <ClerkProvider>. The (app) and
// (auth) route-group layouts mount it; marketing routes therefore SSR to HTML
// containing zero Clerk JS, so marketing pages ship without Clerk runtime.
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <OrganizationJsonLd />
      </head>
      <body>
        <PostHogProvider>{children}</PostHogProvider>
      </body>
    </html>
  )
}
