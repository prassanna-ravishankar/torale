import { cn } from '@/lib/utils'

import styles from '@/components/landing/Landing.module.css'

export function Manifesto() {
  return (
    <section className={styles.section} id="manifesto">
      <div className={cn(styles.container, styles.manifesto)}>
        <div>
          <div className={styles.eyebrow}>Approach</div>
        </div>
        <div>
          <p className={styles.manifestoQuote}>
            The web is not a feed.{' '}
            <span className={styles.manifestoQuoteEm}>
              It's a place where things settle.
            </span>
          </p>
          <p className={styles.manifestoBody} style={{ marginTop: '32px' }}>
            Most monitoring tools are alarms. They buzz when a pixel changes,
            when a status code flips, when anything happens. We think that's
            the wrong job.
          </p>
          <p className={styles.manifestoBody}>
            webwhen is patient. It waits for a specific answer to a specific
            question, and it stays quiet until that answer arrives. The agent
            reads the web the way a careful human would — checks a few sources,
            weighs them, decides whether the question has been answered. When
            it has, it tells you.
          </p>
          <p className={styles.manifestoBody}>
            That's the whole product. No dashboards to keep open. No pixel-diff
            noise. No daily digest you'll learn to ignore.
          </p>
        </div>
      </div>
    </section>
  )
}

export default Manifesto
