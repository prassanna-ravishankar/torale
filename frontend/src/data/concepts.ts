/**
 * Concept data for /concepts/:concept pages. Used by ConceptPage.tsx.
 */

export interface ConceptSection {
  heading: string;
  /** Rendered as <p> in order — plain strings, no markdown. */
  paragraphs: string[];
}

export interface ConceptData {
  name: string;
  tagline: string;
  metaTitle: string;
  metaDescription: string;
  heroTitle: string;
  heroSubtitle: string;
  /** Short lead paragraph rendered above the first section. */
  intro: string;
  /** Ordered long-form sections. */
  sections: ConceptSection[];
  faq: {
    question: string;
    answer: string;
  }[];
  relatedLinks?: {
    href: string;
    label: string;
  }[];
  /** Link to a deeper engineering doc on docs.torale.ai. */
  engineeringDoc?: {
    href: string;
    label: string;
  };
}

export const CONCEPTS: Record<string, ConceptData> = {
  'self-scheduling-agents': {
    name: 'Self-Scheduling Agents',
    tagline: 'Monitoring that decides when to look next',
    metaTitle: 'Self-Scheduling Agents for Web Monitoring | Torale',
    metaDescription:
      "A self-scheduling agent watches the web, reasons about what it finds, and decides when to check again. Torale's agent loop replaces cron + scrape with grounded search and typed decisions.",
    heroTitle: 'Self-Scheduling Agents for Web Monitoring',
    heroSubtitle:
      'An agent that decides what to search, whether the condition is met, and when to run next — without you wiring up cron jobs or diff thresholds.',
    intro:
      "Most web-monitoring tools are glorified cron + diff: check this page every N minutes, fire when bytes change. That breaks on dynamic sites, noisy layouts, and anything that requires interpretation. Torale takes a different shape: each monitoring task runs as a self-scheduling agent that understands the question, searches for current evidence, decides whether the condition is met, and picks its own next check time.",
    sections: [
      {
        heading: 'What is a self-scheduling agent?',
        paragraphs: [
          'A self-scheduling agent is a program that combines three abilities in a single loop: it can perceive (read the web), it can reason (decide what the observation means), and it can schedule its next action. The last part is what makes it self-scheduling — the agent returns when it should be woken up, rather than being pinned to a fixed interval.',
          'Concretely, a Torale agent is a Pydantic AI agent with grounded search tools. It runs on a schedule managed by APScheduler, produces a typed response on every execution, and that response contains a `next_run` timestamp the scheduler respects. When `next_run` is null, the task is done.',
        ],
      },
      {
        heading: 'How it differs from cron + scrape',
        paragraphs: [
          'Traditional monitoring fires on a fixed cadence and compares two snapshots. This produces false positives on trivial layout changes, misses anything gated behind JavaScript it can\'t execute, and has no concept of "the thing I actually care about."',
          'A self-scheduling agent grounds every run in live search results. It searches for fresh evidence, reads the relevant pages, and reasons about whether the user\'s natural-language condition ("Apple has announced a specific release date") is satisfied. The schedule adapts to what the agent finds: a check that turned up clear evidence of "soon" warrants an earlier next run; stale results warrant a longer interval.',
          'The result is fewer false positives, fewer missed signals, and no manual tuning of polling cadence.',
        ],
      },
      {
        heading: "Inside Torale's loop",
        paragraphs: [
          'Each task in Torale is defined by a `search_query` and a `condition_description`. When APScheduler fires a task, the backend invokes the monitoring agent over an A2A (agent-to-agent) protocol. The agent performs grounded search via Gemini, optionally issues broader queries through Parallel Search, fetches specific pages when it needs more context, and synthesises a structured response.',
          'The response is a typed object containing: whether the condition is met, a short human-readable answer, the agent\'s reasoning, citations with clean source URLs, and the next run time. The backend persists all of this, fires notifications when appropriate, and uses `next_run` to reschedule.',
          "When the agent decides the condition is permanently satisfied and `notify_behavior=\"once\"`, it returns `next_run=null`. The backend transitions the task to completed and removes the scheduled job. The user gets exactly one notification; the task stops consuming resources.",
        ],
      },
      {
        heading: 'Where it fits',
        paragraphs: [
          'Self-scheduling agents are the right shape when the "is it true?" question requires interpretation, when the answer may appear on pages you haven\'t enumerated in advance, and when checking too often would be wasteful or rate-limited. Price drop alerts, product launch watches, regulatory announcement monitoring, crypto listing detection, and "did they finally publish the API docs?" all fit this shape.',
          'They\'re the wrong shape when you already know the exact URL and DOM selector, don\'t need interpretation, and the page is stable. A plain scraper is cheaper.',
        ],
      },
    ],
    faq: [
      {
        question: 'How is this different from a scheduled LLM call?',
        answer:
          'A scheduled LLM call runs on a fixed cadence the human picked. A self-scheduling agent picks the cadence itself based on what the last run found — earlier if the evidence is heating up, later if nothing has changed, never if the condition is permanently satisfied.',
      },
      {
        question: 'Does the agent hallucinate answers?',
        answer:
          'The agent is grounded in live search results on every run. Each answer is backed by citations to the pages it read, and the agent\'s reasoning is returned alongside the decision. If a result isn\'t well-supported, the agent says so rather than inventing one.',
      },
      {
        question: 'Is the scheduling really adaptive, or just a timer?',
        answer:
          'It\'s adaptive. The agent returns a `next_run` timestamp as part of its structured response. The backend respects it via APScheduler. You don\'t set "check every 15 minutes" — the agent decides, and the schedule changes as the situation changes.',
      },
      {
        question: 'What happens when the condition is finally met?',
        answer:
          'For `notify_behavior="once"` tasks, the agent returns `next_run=null`. The backend fires one notification (email, webhook, Discord), then transitions the task to completed and stops scheduling it. You get exactly one signal, not hundreds.',
      },
      {
        question: 'Can I use it without writing code?',
        answer:
          'Yes — tasks are created in the Torale web app by describing the query and condition in plain English. There\'s also a Python SDK and a REST API for programmatic use.',
      },
    ],
    relatedLinks: [
      { href: '/compare/visualping-alternative', label: 'vs VisualPing' },
      { href: '/use-cases/crypto-exchange-listing-alert', label: 'Use case: Crypto listing alerts' },
      { href: '/use-cases/steam-game-price-alerts', label: 'Use case: Steam price alerts' },
    ],
    engineeringDoc: {
      href: 'https://docs.torale.ai/architecture/self-scheduling-agents',
      label: 'Engineering deep-dive: torale-agent + APScheduler',
    },
  },
};
