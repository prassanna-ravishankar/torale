import type { Components } from 'react-markdown'

/**
 * Build a constrained `react-markdown` components map matching the contract
 * documented in design/webwhen/README.md (CONTENT RENDERING):
 *
 *   - body-scale prose only: p / strong / em / ul / ol / li
 *   - h1–h6 collapse to <p> (page surface owns the title)
 *   - code/pre stripped to plain text
 *   - img stripped entirely
 *   - a renders link text inert (sources cluster is the link surface)
 *
 * Parameterized by the styles module so callers can route p/ul/li at their
 * own CSS Module classes (different surfaces use different visual register).
 */
export function makeConstrainedMarkdown(styles: {
  paragraph?: string
  list?: string
  listItem?: string
}): Components {
  return {
    h1: ({ children }) => <p className={styles.paragraph}>{children}</p>,
    h2: ({ children }) => <p className={styles.paragraph}>{children}</p>,
    h3: ({ children }) => <p className={styles.paragraph}>{children}</p>,
    h4: ({ children }) => <p className={styles.paragraph}>{children}</p>,
    h5: ({ children }) => <p className={styles.paragraph}>{children}</p>,
    h6: ({ children }) => <p className={styles.paragraph}>{children}</p>,
    p: ({ children }) => <p className={styles.paragraph}>{children}</p>,
    ul: ({ children }) => <ul className={styles.list}>{children}</ul>,
    ol: ({ children }) => <ol className={styles.list}>{children}</ol>,
    li: ({ children }) => <li className={styles.listItem}>{children}</li>,
    code: ({ children }) => <>{children}</>,
    pre: ({ children }) => <>{children}</>,
    img: () => null,
    a: ({ children }) => <span>{children}</span>,
  }
}
