import type { ReactNode } from 'react'

// Marketing route group. NO ClerkProvider, NO auth context. Pure RSC tree
// for SEO/LCP — Clerk SDK is never reachable from this subtree's chunks.
export default function MarketingLayout({ children }: { children: ReactNode }) {
  return <>{children}</>
}
