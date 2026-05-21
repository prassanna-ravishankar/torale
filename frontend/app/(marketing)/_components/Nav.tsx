import Link from 'next/link'

import { cn } from '@/lib/utils'

import styles from '@/components/landing/Landing.module.css'

interface NavProps {
  /**
   * If supplied, used to determine the active top-level link (e.g.
   * `/use-cases`, `/compare`). Pass an empty string to disable highlighting
   * (e.g. on Landing where the nav links are in-page anchors).
   */
  activePath?: string
}

const TOP_LEVEL_LINKS: Array<{ href: string; label: string; matchPath?: string }> = [
  { href: '#how', label: 'How it works' },
  { href: '#cases', label: 'Use cases', matchPath: '/use-cases' },
  { href: '#manifesto', label: 'Approach', matchPath: '/concepts' },
]

// Anonymous-only nav for the marketing tree. The auth-aware Dashboard CTA
// will be reintroduced when the (app) route-group ships its own auth-aware
// header (#334 commit 3). Until then marketing always renders the
// signed-out variant — matches the PR #337 pre-Clerk-hydrate state.
export function Nav({ activePath }: NavProps) {
  const path = activePath ?? ''

  return (
    <nav className={styles.nav}>
      <div className={cn(styles.container, styles.navRow)}>
        <div className={styles.navLeft}>
          <Link href="/" className={styles.brand}>
            <img
              src="/brand/webwhen-mark.svg"
              alt="webwhen"
              width={26}
              height={26}
              className={styles.brandImg}
            />
            <span className={styles.brandWord}>webwhen</span>
          </Link>
          <div className={styles.navLinks}>
            {TOP_LEVEL_LINKS.map((link) => {
              const isActive = link.matchPath ? path.startsWith(link.matchPath) : false
              return (
                <a
                  key={link.label}
                  href={link.href}
                  className={styles.navLink}
                  aria-current={isActive ? 'page' : undefined}
                  style={isActive ? { color: 'var(--ww-ink-0)' } : undefined}
                >
                  {link.label}
                </a>
              )
            })}
          </div>
        </div>
        <div className={styles.navRight}>
          <Link href="/sign-in" className={cn(styles.btn, styles.btnGhost)}>
            Sign in
          </Link>
          <Link href="/sign-up" className={cn(styles.btn, styles.btnPrimary)}>
            Start watching <span style={{ fontFamily: 'var(--ww-font-mono)' }}>→</span>
          </Link>
        </div>
      </div>
    </nav>
  )
}

export default Nav
