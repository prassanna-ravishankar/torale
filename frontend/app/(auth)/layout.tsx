import type { ReactNode } from 'react'

// Auth route group. ClerkProvider mounts here in commit 3 for the Clerk
// catch-all sign-in/sign-up surfaces.
export default function AuthLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}
