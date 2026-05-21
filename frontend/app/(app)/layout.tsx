import type { ReactNode } from 'react'

// App route group. ClerkProvider mounts here in commit 3. Until then this
// is a transparent passthrough so the scaffold compiles.
export default function AppLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}
