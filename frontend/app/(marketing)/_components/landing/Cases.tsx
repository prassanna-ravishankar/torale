'use client'

import { useLandingExamples } from './LandingExamplesContext'
import { cn } from '@/lib/utils'

import styles from '@/components/landing/Landing.module.css'

function shortDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function Cases() {
  const { cases } = useLandingExamples()

  if (cases.length === 0) return null

  return (
    <section className={cn(styles.section, styles.sectionAlt)} id="cases">
      <div className={styles.container}>
        <div className={styles.eyebrow}>Receipts</div>
        <h2 className={styles.sectionHeading}>
          If it lives on the open web,{' '}
          <span className={styles.sectionHeadingAccent}>
            webwhen can wait for it.
          </span>
        </h2>
        <div className={styles.cases}>
          {cases.map((entry) => {
            const settled = entry.state === 'completed'
            const stateLabel = settled ? 'settled' : 'watching'
            const date = shortDate(entry.startedAt)
            return (
              <article key={entry.taskId} className={styles.caseCard}>
                <div className={styles.caseTag}>{entry.tag}</div>
                <p className={styles.caseQuestion}>{entry.displayPrompt}</p>
                {entry.evidence && (
                  <p className={styles.caseEvidence}>{entry.evidence}</p>
                )}
                {entry.sources.length > 0 && (
                  <div className={styles.caseSources}>
                    {entry.sources.join(' · ')}
                  </div>
                )}
                <div className={styles.caseResult}>
                  <span
                    className={cn(
                      styles.caseState,
                      settled && styles.caseStateSettled,
                    )}
                  >
                    <span className={styles.caseStateDot}></span>
                    {stateLabel}
                  </span>
                  {date && <span>{date}</span>}
                </div>
              </article>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export default Cases
