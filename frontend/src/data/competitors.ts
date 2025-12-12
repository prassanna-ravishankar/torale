/**
 * Competitor comparison data for SEO landing pages
 * Used by ComparePage.tsx
 */

export interface CompetitorData {
  name: string;
  tagline: string;
  description: string;
  metaTitle: string;
  metaDescription: string;
  heroTitle: string;
  heroSubtitle: string;
  competitorName: string;
  competitorStrengths: string[];
  toraleAdvantages: string[];
  comparisonTable: {
    feature: string;
    competitor: string | boolean;
    torale: string | boolean;
  }[];
  useCases: {
    title: string;
    description: string;
    example: string;
  }[];
  faq: {
    question: string;
    answer: string;
  }[];
}

export const COMPETITORS: Record<string, CompetitorData> = {
  'visualping-alternative': {
    name: 'VisualPing',
    tagline: 'AI-Powered Alternative to VisualPing',
    description: 'Looking for a smarter alternative to VisualPing? Torale uses AI to understand semantic changes, not just visual diffs.',
    metaTitle: 'Best VisualPing Alternative - AI-Powered Web Monitoring | Torale',
    metaDescription: 'Torale offers AI-powered conditional monitoring vs VisualPing\'s visual diffs. Monitor semantic changes like "price drops below $500" instead of just "page changed".',
    heroTitle: 'Looking for a VisualPing Alternative?',
    heroSubtitle: 'Go beyond visual diffs with AI-powered conditional monitoring',
    competitorName: 'VisualPing',
    competitorStrengths: [
      'Easy visual comparison',
      'Browser extension',
      'Simple screenshot-based monitoring'
    ],
    toraleAdvantages: [
      'AI understands semantic meaning ("price dropped" vs "CSS changed")',
      'Natural language conditions: "Alert when release date announced"',
      'Structured data extraction from unstructured pages',
      'Developer-first: Python SDK, webhooks, JSON responses',
      'Free while in beta'
    ],
    comparisonTable: [
      { feature: 'Monitoring Type', competitor: 'Visual diff (screenshots)', torale: 'Semantic understanding (LLM)' },
      { feature: 'Condition Logic', competitor: 'Text changed', torale: 'Natural language conditions' },
      { feature: 'False Positives', competitor: 'CSS/layout changes trigger', torale: 'Ignores styling, focuses on meaning' },
      { feature: 'Data Extraction', competitor: false, torale: 'Structured data (prices, dates)' },
      { feature: 'Developer API', competitor: 'Limited', torale: 'Full Python SDK + webhooks' },
      { feature: 'Pricing', competitor: 'Paid plans', torale: 'Free beta' }
    ],
    useCases: [
      {
        title: 'Smart Price Monitoring',
        description: 'VisualPing alerts on any page change. Torale only alerts when the actual price drops.',
        example: '"Alert when competitor\'s Enterprise plan drops below $99/month"'
      },
      {
        title: 'Product Availability',
        description: 'Detect specific variants back in stock, not just page updates.',
        example: '"Notify when iPhone 15 Pro in Natural Titanium 256GB is available"'
      },
      {
        title: 'Release Date Tracking',
        description: 'Know when a date is announced, not just when the page changes.',
        example: '"Alert when GPT-5 launch date is confirmed"'
      }
    ],
    faq: [
      {
        question: 'How is Torale different from VisualPing?',
        answer: 'VisualPing uses visual diffs (screenshots) to detect any pixel change. Torale uses AI to understand semantic meaning - it knows the difference between a price drop and a CSS change.'
      },
      {
        question: 'Will I get fewer false positives?',
        answer: 'Yes! Torale filters out noise like styling changes, timestamp updates, and layout shifts. You only get alerted when meaningful conditions are met.'
      },
      {
        question: 'Can I migrate from VisualPing to Torale?',
        answer: 'Absolutely! Torale is designed to be more developer-friendly with better API access and webhooks for automation.'
      }
    ]
  },
  'distill-alternative': {
    name: 'Distill.io',
    tagline: 'AI-Powered Alternative to Distill.io',
    description: 'Upgrade from Distill.io\'s text change detection to Torale\'s AI-powered semantic monitoring.',
    metaTitle: 'Best Distill.io Alternative - Semantic Web Monitoring | Torale',
    metaDescription: 'Torale offers AI-powered conditional monitoring vs Distill.io\'s text diffs. Better for developers with Python SDK, webhooks, and structured JSON responses.',
    heroTitle: 'Looking for a Distill.io Alternative?',
    heroSubtitle: 'AI-powered monitoring with developer-first APIs',
    competitorName: 'Distill.io',
    competitorStrengths: [
      'Chrome extension',
      'Local monitoring option',
      'Email notifications'
    ],
    toraleAdvantages: [
      'Semantic understanding vs text diffs',
      'Python SDK for automation',
      'Webhook integrations with structured payloads',
      'Natural language conditions',
      'Better for developers'
    ],
    comparisonTable: [
      { feature: 'Detection Method', competitor: 'Text diff', torale: 'AI semantic analysis' },
      { feature: 'Python SDK', competitor: false, torale: true },
      { feature: 'Webhooks', competitor: 'Basic', torale: 'Advanced with JSON payloads' },
      { feature: 'Condition Logic', competitor: 'Regex patterns', torale: 'Natural language' },
      { feature: 'Structured Data', competitor: false, torale: 'Extract prices, dates, etc.' },
      { feature: 'Source Attribution', competitor: false, torale: 'Grounding sources included' }
    ],
    useCases: [
      {
        title: 'API Deprecation Monitoring',
        description: 'Monitor developer blogs for breaking changes, not just any update.',
        example: '"Alert when Stripe deprecates v1 API"'
      },
      {
        title: 'Competitor Feature Launches',
        description: 'Detect when competitors add specific features like SSO.',
        example: '"Notify when competitor adds SAML authentication"'
      },
      {
        title: 'Developer Automation',
        description: 'Use Python SDK to build custom monitoring workflows.',
        example: 'Webhook → Slack → PagerDuty integration'
      }
    ],
    faq: [
      {
        question: 'Is Torale better for developers than Distill.io?',
        answer: 'Yes! Torale offers a full Python SDK, advanced webhooks with structured JSON, and natural language conditions instead of regex patterns.'
      },
      {
        question: 'Can I get structured data from monitored pages?',
        answer: 'Absolutely. Torale extracts structured data (prices, dates, availability) from unstructured web pages using AI.'
      },
      {
        question: 'Does Torale support webhooks?',
        answer: 'Yes, with detailed JSON payloads including the change summary, grounding sources, and extracted state.'
      }
    ]
  },
  'changetower-alternative': {
    name: 'ChangeTower',
    tagline: 'AI-Powered Alternative to ChangeTower',
    description: 'More powerful than ChangeTower with AI-driven conditional monitoring and free beta access.',
    metaTitle: 'Best ChangeTower Alternative - AI Web Monitoring | Torale',
    metaDescription: 'Torale offers AI-powered semantic monitoring vs ChangeTower\'s text detection. Free beta with more powerful conditional logic.',
    heroTitle: 'Looking for a ChangeTower Alternative?',
    heroSubtitle: 'More powerful AI monitoring, free while in beta',
    competitorName: 'ChangeTower',
    competitorStrengths: [
      'SEO monitoring features',
      'Team collaboration',
      'Email reports'
    ],
    toraleAdvantages: [
      'AI-powered semantic understanding',
      'Free while in beta (vs paid plans)',
      'Natural language conditions',
      'Developer SDK and webhooks',
      'More powerful condition logic'
    ],
    comparisonTable: [
      { feature: 'AI Understanding', competitor: false, torale: true },
      { feature: 'Natural Language', competitor: false, torale: 'Full LLM-based conditions' },
      { feature: 'Developer API', competitor: 'Basic', torale: 'Python SDK + webhooks' },
      { feature: 'Pricing', competitor: 'Paid plans', torale: 'Free beta' },
      { feature: 'State Tracking', competitor: 'Basic', torale: 'Advanced with comparison' },
      { feature: 'Source Attribution', competitor: false, torale: 'Grounding sources' }
    ],
    useCases: [
      {
        title: 'SEO Competitor Monitoring',
        description: 'Track when competitors rank for your target keywords.',
        example: '"Alert when competitor ranks top 3 for \'AI monitoring tools\'"'
      },
      {
        title: 'Content Change Detection',
        description: 'Know when competitors update pricing or features.',
        example: '"Notify when competitor removes \'Free Tier\' from pricing"'
      },
      {
        title: 'Technical Monitoring',
        description: 'Monitor APIs, status pages, and technical resources.',
        example: '"Alert when AWS status page shows \'Degraded\' for us-east-1"'
      }
    ],
    faq: [
      {
        question: 'How is Torale more powerful than ChangeTower?',
        answer: 'Torale uses AI to understand context and meaning, not just text changes. This means fewer false positives and more accurate condition detection.'
      },
      {
        question: 'Is Torale really free?',
        answer: 'Yes! Torale is free while in beta. We\'ll announce pricing before any changes.'
      },
      {
        question: 'Can I use Torale for SEO monitoring?',
        answer: 'Absolutely. Monitor competitor rankings, content changes, and keyword performance with natural language conditions.'
      }
    ]
  }
};
