import type { Metadata } from 'next'
import type { ReactNode } from 'react'
// globals.css is imported here so the App Router tree gets fonts + tokens.
// During scaffold commit this re-exports the existing index.css; once the
// Vite tree is deleted (commit 6) we'll rename in place.
import '../src/index.css'
import { OrganizationJsonLd } from '../components/seo/OrganizationJsonLd'
import { PostHogProvider } from '../components/analytics/PostHogProvider'

// Root metadata — per-page metadata in (marketing)/* and (app)/* overrides
// title via `template`. See app/(marketing)/page.tsx etc.
export const metadata: Metadata = {
  title: {
    default: 'webwhen — the agent that waits for the web',
    template: '%s · webwhen',
  },
  description:
    'Tell webwhen what to watch for in plain English. It will sit with the question, search the web on a schedule, and tell you the moment your condition is met.',
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_ORIGIN || 'https://webwhen.ai',
  ),
}

// Root layout intentionally does NOT mount <ClerkProvider>. The (app) and
// (auth) route-group layouts mount it; marketing routes therefore SSR to HTML
// containing zero Clerk JS, preserving the PR #337 LCP invariant as a
// structural property.
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
