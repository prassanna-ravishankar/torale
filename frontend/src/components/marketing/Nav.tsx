'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'

import styles from '../landing/Landing.module.css'

interface NavProps {
  /**
   * If supplied, used to determine the active top-level link (e.g. `/use-cases`,
   * `/compare`). When absent, derived from `useLocation()`.
   *
   * Pass an empty string to disable highlighting (e.g. on Landing where the
   * nav links are in-page anchors).
   */
  activePath?: string
}

const TOP_LEVEL_LINKS: Array<{ href: string; label: string; matchPath?: string }> = [
  { href: '#how', label: 'How it works' },
  { href: '#cases', label: 'Use cases', matchPath: '/use-cases' },
  { href: '#manifesto', label: 'Approach', matchPath: '/concepts' },
]

export const Nav: React.FC<NavProps> = ({ activePath }) => {
  const { user } = useAuth()
  const pathname = usePathname() || ''
  const path = activePath ?? pathname

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
          {user ? (
            <Link href="/dashboard" className={cn(styles.btn, styles.btnPrimary)}>
              Dashboard <span style={{ fontFamily: 'var(--ww-font-mono)' }}>→</span>
            </Link>
          ) : (
            <>
              <Link href="/sign-in" className={cn(styles.btn, styles.btnGhost)}>
                Sign in
              </Link>
              <Link href="/sign-up" className={cn(styles.btn, styles.btnPrimary)}>
                Start watching <span style={{ fontFamily: 'var(--ww-font-mono)' }}>→</span>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Nav
