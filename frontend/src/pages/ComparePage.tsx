import { useParams, Navigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { CheckCircle2, XCircle, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

/**
 * Comparison page for Torale vs competitors
 * Routes: /compare/visualping-alternative, /compare/distill-alternative, etc.
 */

interface CompetitorData {
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

const COMPETITORS: Record<string, CompetitorData> = {
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

export function ComparePage() {
  const { tool } = useParams<{ tool: string }>();
  const navigate = useNavigate();

  if (!tool || !COMPETITORS[tool]) {
    return <Navigate to="/" replace />;
  }

  const data = COMPETITORS[tool];

  return (
    <>
      <Helmet>
        <title>{data.metaTitle}</title>
        <meta name="description" content={data.metaDescription} />
        <meta property="og:title" content={data.metaTitle} />
        <meta property="og:description" content={data.metaDescription} />
        <meta property="og:type" content="article" />
      </Helmet>

      <div className="min-h-screen bg-[#fafafa]">
        {/* Hero Section */}
        <section className="relative pt-32 pb-24 px-6 border-b border-zinc-200">
          <div className="container mx-auto max-w-4xl text-center">
            <div className="mb-8">
              <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border-2 border-zinc-900 text-zinc-900 text-xs font-mono font-bold uppercase tracking-wider shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                Free Beta
              </span>
            </div>

            <h1 className="text-5xl md:text-6xl font-bold font-grotesk tracking-tight mb-6 text-zinc-900">
              {data.heroTitle}
            </h1>

            <p className="text-xl text-zinc-500 mb-10 max-w-2xl mx-auto">
              {data.heroSubtitle}
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => navigate('/dashboard')}
                className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-[hsl(10,90%,55%)] text-white text-lg font-bold hover:bg-[hsl(10,90%,50%)] transition-all shadow-[6px_6px_0px_0px_rgba(24,24,27,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(24,24,27,1)] border-2 border-zinc-900"
              >
                Try Torale Free
                <ArrowRight className="h-5 w-5" />
              </button>
            </div>
          </div>
        </section>

        {/* Why Torale Section */}
        <section className="py-24 px-6 bg-white">
          <div className="container mx-auto max-w-4xl">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-8 text-zinc-900">
              Why Choose Torale Over {data.competitorName}?
            </h2>

            <div className="space-y-4">
              {data.toraleAdvantages.map((advantage, idx) => (
                <div key={idx} className="flex items-start gap-3 p-4 bg-emerald-50 border-l-4 border-emerald-500">
                  <CheckCircle2 className="h-6 w-6 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <p className="text-zinc-700 font-medium">{advantage}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Comparison Table */}
        <section className="py-24 px-6 bg-zinc-50">
          <div className="container mx-auto max-w-4xl">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-12 text-zinc-900 text-center">
              Feature Comparison
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full border-2 border-zinc-900 bg-white">
                <thead>
                  <tr className="border-b-2 border-zinc-900">
                    <th className="px-6 py-4 text-left font-bold text-zinc-900 border-r-2 border-zinc-900">Feature</th>
                    <th className="px-6 py-4 text-left font-bold text-zinc-900 border-r-2 border-zinc-900">{data.competitorName}</th>
                    <th className="px-6 py-4 text-left font-bold text-zinc-900">Torale</th>
                  </tr>
                </thead>
                <tbody>
                  {data.comparisonTable.map((row, idx) => (
                    <tr key={idx} className="border-b border-zinc-200 last:border-0">
                      <td className="px-6 py-4 font-medium text-zinc-900 border-r-2 border-zinc-200">{row.feature}</td>
                      <td className="px-6 py-4 text-zinc-600 border-r-2 border-zinc-200">
                        {typeof row.competitor === 'boolean' ? (
                          row.competitor ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <XCircle className="h-5 w-5 text-zinc-300" />
                        ) : row.competitor}
                      </td>
                      <td className="px-6 py-4 text-zinc-600">
                        {typeof row.torale === 'boolean' ? (
                          row.torale ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <XCircle className="h-5 w-5 text-zinc-300" />
                        ) : row.torale}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Use Cases */}
        <section className="py-24 px-6 bg-white">
          <div className="container mx-auto max-w-4xl">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-12 text-zinc-900">
              Use Cases Where Torale Excels
            </h2>

            <div className="grid gap-8">
              {data.useCases.map((useCase, idx) => (
                <div key={idx} className="p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-colors">
                  <h3 className="text-xl font-bold font-grotesk text-zinc-900 mb-3">{useCase.title}</h3>
                  <p className="text-zinc-600 mb-4">{useCase.description}</p>
                  <div className="bg-zinc-50 p-4 border-l-4 border-emerald-500 font-mono text-sm text-zinc-700">
                    {useCase.example}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section className="py-24 px-6 bg-zinc-50">
          <div className="container mx-auto max-w-3xl">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-12 text-zinc-900 text-center">
              Frequently Asked Questions
            </h2>

            <div className="space-y-8">
              {data.faq.map((item, idx) => (
                <div key={idx}>
                  <h3 className="text-xl font-bold text-zinc-900 mb-3">{item.question}</h3>
                  <p className="text-zinc-600 leading-relaxed">{item.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24 px-6 bg-zinc-900 text-white">
          <div className="container mx-auto max-w-3xl text-center">
            <h2 className="text-3xl md:text-4xl font-bold font-grotesk mb-6">
              Ready to Try Torale?
            </h2>
            <p className="text-xl text-zinc-300 mb-10">
              Join free beta and experience AI-powered web monitoring
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-[hsl(10,90%,55%)] text-white text-lg font-bold hover:bg-[hsl(10,90%,50%)] transition-all shadow-[6px_6px_0px_0px_rgba(255,255,255,0.1)]"
            >
              Start Monitoring Free
              <ArrowRight className="h-5 w-5" />
            </button>
          </div>
        </section>
      </div>
    </>
  );
}
