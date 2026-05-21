import Link from 'next/link'

import { cn } from '@/lib/utils'

import styles from '../landing/Landing.module.css'

export const Footer: React.FC = () => {
  return (
    <footer className={styles.footer}>
      <div className={cn(styles.container, styles.footerGrid)}>
        <div>
          <Link href="/" className={styles.brand}>
            <img
              src="/brand/webwhen-mark-dark.svg"
              alt="webwhen"
              width={26}
              height={26}
              className={styles.brandImg}
            />
            <span className={styles.brandWord}>webwhen</span>
          </Link>
          <p
            style={{
              color: 'var(--ww-ink-4)',
              fontSize: '14px',
              maxWidth: '24ch',
              marginTop: '16px',
            }}
          >
            The agent that waits for the web.
          </p>
        </div>
        <div>
          <h4 className={styles.footerHeading}>Product</h4>
          <ul className={styles.footerList}>
            <li className={styles.footerListItem}>
              <Link href="/explore">Explore</Link>
            </li>
            <li className={styles.footerListItem}>
              <Link href="/changelog">Changelog</Link>
            </li>
            <li className={styles.footerListItem}>
              <Link href="/concepts/self-scheduling-agents">Self-scheduling agents</Link>
            </li>
          </ul>
        </div>
        <div>
          <h4 className={styles.footerHeading}>Compare</h4>
          <ul className={styles.footerList}>
            <li className={styles.footerListItem}>
              <Link href="/compare/visualping-alternative">vs VisualPing</Link>
            </li>
            <li className={styles.footerListItem}>
              <Link href="/compare/distill-alternative">vs Distill</Link>
            </li>
            <li className={styles.footerListItem}>
              <Link href="/compare/changetower-alternative">vs ChangeTower</Link>
            </li>
          </ul>
        </div>
        <div>
          <h4 className={styles.footerHeading}>Resources</h4>
          <ul className={styles.footerList}>
            <li className={styles.footerListItem}>
              <a href="https://docs.webwhen.ai">Docs</a>
            </li>
            <li className={styles.footerListItem}>
              <a href="https://github.com/prassanna-ravishankar/webwhen">GitHub</a>
            </li>
          </ul>
        </div>
        <div>
          <h4 className={styles.footerHeading}>Use cases</h4>
          <ul className={styles.footerList}>
            <li className={styles.footerListItem}>
              <Link href="/use-cases/steam-game-price-alerts">Steam game prices</Link>
            </li>
            <li className={styles.footerListItem}>
              <Link href="/use-cases/competitor-price-change-monitor">Competitor pricing</Link>
            </li>
            <li className={styles.footerListItem}>
              <Link href="/use-cases/crypto-exchange-listing-alert">Crypto listings</Link>
            </li>
          </ul>
        </div>
        <div>
          <h4 className={styles.footerHeading}>Company</h4>
          <ul className={styles.footerList}>
            <li className={styles.footerListItem}>
              <Link href="/privacy">Privacy</Link>
            </li>
            <li className={styles.footerListItem}>
              <Link href="/terms">Terms</Link>
            </li>
          </ul>
        </div>
      </div>
      <div className={cn(styles.container, styles.footerRow2)}>
        <span style={{ color: 'var(--ww-ink-4)', fontSize: '13px' }}>© 2026 webwhen</span>
      </div>
    </footer>
  )
}

export default Footer
