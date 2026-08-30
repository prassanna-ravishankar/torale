import type { ReactNode } from 'react'
import { ClerkProvider } from '@clerk/nextjs'

// Clerk's <SignIn>/<SignUp> read cookies + must not be prerendered with a
// placeholder publishable key during build.
export const dynamic = 'force-dynamic'


// The (auth) route group hosts Clerk's <SignIn> / <SignUp> catch-all surfaces.
// Wrapping in a centered card mirrors the App.tsx-era AuthLayout.
function AuthCard({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30">
      {children}
    </div>
  )
}

export default function AuthLayout({ children }: { children: ReactNode }) {
  if (process.env.NEXT_PUBLIC_WEBWHEN_NOAUTH === '1') {
    return <AuthCard>{children}</AuthCard>
  }
  return (
    <ClerkProvider waitlistUrl="/waitlist">
      <AuthCard>{children}</AuthCard>
    </ClerkProvider>
  )
}
