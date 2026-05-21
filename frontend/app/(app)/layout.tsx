import type { ReactNode } from 'react'
import { ClerkProvider } from '@clerk/nextjs'

// Every page under (app) is authenticated and must render per-request — the
// middleware enforces auth and Clerk session state can't be prerendered.
export const dynamic = 'force-dynamic'

import { AuthProvider } from '@/contexts/AuthContext'
import { NoAuthProvider } from '@/contexts/NoAuthProvider'
import { AuthedApiBootstrap } from './AuthedApiBootstrap'

// The (app) route group is the only place (alongside (auth)) where Clerk
// mounts. Marketing routes live outside this subtree and never load Clerk JS,
// preserving the PR #337 LCP invariant as a structural property of the build.
//
// NEXT_PUBLIC_WEBWHEN_NOAUTH=1 is the local-dev escape hatch: skip Clerk
// entirely and render a stable mock user via NoAuthProvider.
export default function AppLayout({ children }: { children: ReactNode }) {
  if (process.env.NEXT_PUBLIC_WEBWHEN_NOAUTH === '1') {
    return (
      <NoAuthProvider>
        <AuthedApiBootstrap>{children}</AuthedApiBootstrap>
      </NoAuthProvider>
    )
  }
  return (
    <ClerkProvider waitlistUrl="/waitlist">
      <AuthProvider>
        <AuthedApiBootstrap>{children}</AuthedApiBootstrap>
      </AuthProvider>
    </ClerkProvider>
  )
}
