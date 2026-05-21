import styles from '@/components/landing/Landing.module.css'

export function Steps() {
  return (
    <section className={styles.section} id="how">
      <div className={styles.container}>
        <div className={styles.eyebrow}>How it works</div>
        <h2 className={styles.sectionHeading}>
          You set the condition.{' '}
          <span className={styles.sectionHeadingAccent}>
            webwhen does the rest.
          </span>
        </h2>
        <div className={styles.steps}>
          <div className={styles.step}>
            <div className={styles.stepNum}>01 / describe</div>
            <h3 className={styles.stepHeading}>Describe the condition.</h3>
            <p className={styles.stepBody}>
              Plain English. No XPath, no regex, no flaky CSS selectors. Just
              say what you're waiting for.
            </p>
            <div className={styles.stepHint}>
              Tell me when the next iPhone release date is announced.
            </div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>02 / settle</div>
            <h3 className={styles.stepHeading}>The agent settles in.</h3>
            <p className={styles.stepBody}>
              webwhen searches across the open web, evaluates evidence against
              your condition, and remembers what it already knew.
            </p>
            <div className={styles.stepHint}>
              searches · evaluates · remembers · waits
            </div>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>03 / the moment</div>
            <h3 className={styles.stepHeading}>
              You hear from it when it has something to say.
            </h3>
            <p className={styles.stepBody}>
              The agent decides when to speak. The condition is met, you get
              the answer and the sources. No false positives, no daily digest
              you'll learn to ignore.
            </p>
            <div className={styles.stepHint}>
              the agent <span className={styles.stepHintEm}>decides</span> · you
              just listen
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Steps
