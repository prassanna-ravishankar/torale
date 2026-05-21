'use client'

import { Menu } from 'lucide-react'
import Link from 'next/link'

import { cn } from '@/lib/utils'

import styles from './AppShell.module.css'

export interface Crumb {
  label: string
  href?: string
}

interface TopbarProps {
  crumbs: Crumb[]
  actions?: React.ReactNode
  onHamburger: () => void
}

/**
 * Sticky 56px topbar. Left: hamburger (mobile) + breadcrumbs (intermediate
 * crumbs as plain links/text + last crumb in italic-serif as the current
 * "you are here" marker). Right: actions slot (page-supplied buttons).
 */
export const Topbar: React.FC<TopbarProps> = ({ crumbs, actions, onHamburger }) => {
  return (
    <div className={styles.topbar}>
      <div className={styles.topbarLeft}>
        <button
          type="button"
          className={styles.hamburger}
          onClick={onHamburger}
          aria-label="Open menu"
        >
          <Menu size={18} strokeWidth={1.5} />
        </button>
        <nav className={styles.crumbs} aria-label="Breadcrumb">
          {crumbs.map((c, i) => {
            const isLast = i === crumbs.length - 1
            const sep = !isLast ? (
              <span key={`sep-${i}`} className={styles.crumbSep}>
                /
              </span>
            ) : null
            const node = isLast ? (
              <span key={c.label} className={styles.crumbHere}>
                {c.label}
              </span>
            ) : c.href ? (
              <Link key={c.label} href={c.href} className={styles.crumbLink}>
                {c.label}
              </Link>
            ) : (
              <span key={c.label} className={styles.crumbLink}>
                {c.label}
              </span>
            )
            return (
              <span key={`crumb-${i}`} className={cn()}>
                {node}
                {sep}
              </span>
            )
          })}
        </nav>
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </div>
  )
}

export default Topbar
