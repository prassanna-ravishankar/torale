import type { ReactNode } from 'react'

import { Nav } from './Nav'
import { Footer } from './Footer'

interface MarketingLayoutProps {
  children: ReactNode
  /**
   * Active path for nav link highlighting. Pass an empty string to disable
   * highlighting (e.g. on Landing where the links are in-page anchors).
   */
  activePath?: string
}

/**
 * Shell wrapper for every public marketing page. Provides the dotted
 * background, sticky Nav and the dark Footer — same surface as the Vite-era
 * src/components/marketing/MarketingLayout.tsx but rebuilt for the App Router
 * so the marketing tree stays Clerk-free.
 */
export function MarketingLayout({ children, activePath }: MarketingLayoutProps) {
  return (
    <>
      <div className="dot-bg" />
      <Nav activePath={activePath} />
      <main>{children}</main>
      <Footer />
    </>
  )
}

export default MarketingLayout
