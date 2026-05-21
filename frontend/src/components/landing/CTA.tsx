import Link from 'next/link'

import { cn } from '@/lib/utils'

import styles from './Landing.module.css'

export const CTA: React.FC = () => {
  return (
    <section className={cn(styles.section, styles.cta)}>
      <div className={styles.container}>
        <h2 className={styles.ctaHeading}>
          What are you waiting <span className={styles.heroEmber}>for</span>?
        </h2>
        <p className={styles.ctaBody}>
          Free while in beta. No credit card. One condition takes about 30 seconds to set up.
        </p>
        <Link href="/sign-up" className={cn(styles.btn, styles.btnPrimary, styles.btnLg)}>
          Start watching <span style={{ fontFamily: 'var(--ww-font-mono)' }}>→</span>
        </Link>
      </div>
    </section>
  )
}

export default CTA
