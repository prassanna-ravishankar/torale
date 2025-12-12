import { useParams, Navigate, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from '@/lib/motion-compat';
import { CheckCircle2, ArrowRight, Zap, Shield, Clock } from 'lucide-react';

/**
 * Use case landing page for Torale
 * Routes: /use-cases/steam-game-price-alerts, /use-cases/competitor-price-change-monitor, etc.
 */

interface UseCaseData {
  name: string;
  tagline: string;
  metaTitle: string;
  metaDescription: string;
  heroTitle: string;
  heroSubtitle: string;
  targetKeyword: string;
  problemStatement: string;
  solutionStatement: string;
  benefits: {
    icon: 'zap' | 'shield' | 'clock';
    title: string;
    description: string;
  }[];
  howItWorks: {
    step: number;
    title: string;
    description: string;
    example: string;
  }[];
  exampleConditions: {
    title: string;
    condition: string;
    result: string;
  }[];
  testimonial?: {
    quote: string;
    author: string;
    role: string;
  };
  faq: {
    question: string;
    answer: string;
  }[];
  relatedUseCases?: string[];
}

const USE_CASES: Record<string, UseCaseData> = {
  'steam-game-price-alerts': {
    name: 'Steam Game Price Alerts',
    tagline: 'Save 50-80% on AAA Titles Automatically',
    metaTitle: 'Steam Game Price Tracker & Alert Tool - Torale',
    metaDescription: 'Get instant alerts when Steam games drop to your target price. Stop overpaying for games you\'ll play once. AI-powered price monitoring for gamers.',
    heroTitle: 'Stop Overpaying for Games You\'ll Play Once',
    heroSubtitle: 'Get notified the second your wishlist games hit your target price on Steam',
    targetKeyword: 'steam game price tracker alert',
    problemStatement: 'Steam sales are great, but checking prices manually is tedious. You either overpay for games at launch or miss limited-time deals while you sleep.',
    solutionStatement: 'Torale monitors Steam pricing 24/7 using AI that understands sale patterns, regional pricing, and bundle deals. Get instant notifications when your wishlist games hit your price target.',
    benefits: [
      {
        icon: 'zap',
        title: 'Instant Alerts',
        description: 'Get notified within minutes when game prices drop to your target',
      },
      {
        icon: 'shield',
        title: 'Smart Filtering',
        description: 'AI distinguishes real sales from regional pricing or DLC bundles',
      },
      {
        icon: 'clock',
        title: 'Never Miss Sales',
        description: '24/7 monitoring catches flash sales even while you sleep',
      },
    ],
    howItWorks: [
      {
        step: 1,
        title: 'Set Your Target Price',
        description: 'Tell Torale which games you want and your maximum price',
        example: '"Elden Ring for under $30"',
      },
      {
        step: 2,
        title: 'AI Monitors Steam 24/7',
        description: 'Torale checks prices continuously using semantic understanding',
        example: 'Distinguishes "base game" from "deluxe edition" pricing',
      },
      {
        step: 3,
        title: 'Get Instant Notifications',
        description: 'Receive email, webhook, or Discord notification when condition is met',
        example: 'Buy immediately before sale ends',
      },
    ],
    exampleConditions: [
      {
        title: 'Single Game Tracker',
        condition: 'Alert me when Elden Ring drops below $30 on Steam',
        result: 'Saved $40 by buying at summer sale',
      },
      {
        title: 'Genre Sale Watcher',
        condition: 'Notify when indie roguelikes go on sale for <$10',
        result: 'Discovered 15 hidden gems during Steam Next Fest',
      },
      {
        title: 'Wishlist Bulk Monitor',
        condition: 'Track my top 20 wishlist games for 50%+ discounts',
        result: 'Spent $200 instead of $800 on backlog',
      },
    ],
    faq: [
      {
        question: 'How is this different from IsThereAnyDeal or SteamDB?',
        answer: 'While those tools require manual checking, Torale sends you instant notifications using AI that understands semantic pricing changes (not just number changes). For example, it knows the difference between a "base game discount" and a "DLC bundle price change."',
      },
      {
        question: 'Can I monitor multiple games at once?',
        answer: 'Yes! You can set up unlimited monitoring tasks. Track your entire wishlist, specific genres, or even competitor pricing across different platforms.',
      },
      {
        question: 'What if the price drops for only a few hours?',
        answer: 'Torale monitors continuously and sends instant notifications. You\'ll get alerted within minutes of a price drop, even during flash sales.',
      },
      {
        question: 'Does this work with regional pricing?',
        answer: 'Yes, Torale\'s AI understands regional pricing variations and can monitor specific regions. You can set conditions like "US price below $30" to avoid false positives from other regions.',
      },
    ],
    relatedUseCases: ['crypto-exchange-listing-alert', 'competitor-price-change-monitor'],
  },
  'competitor-price-change-monitor': {
    name: 'Competitor Price Monitoring',
    tagline: 'React to Market Changes Before You Lose Deals',
    metaTitle: 'Competitor Price Tracking & Monitoring Tool - Torale',
    metaDescription: 'AI-powered competitor price monitoring for SaaS and e-commerce. Get instant alerts when competitors change pricing. Stop losing deals to undercutting.',
    heroTitle: 'Your Competitor Just Lowered Their Price. Did You?',
    heroSubtitle: 'React instantly to market undercutting before you lose your next three deals',
    targetKeyword: 'monitor competitor pricing strategy tools',
    problemStatement: 'Competitors change pricing constantly. By the time you notice, you\'ve already lost deals. Manual checking is impossible at scale.',
    solutionStatement: 'Torale uses AI to monitor competitor pricing pages 24/7, understanding complex pricing structures like tiered plans, volume discounts, and promotional pricing.',
    benefits: [
      {
        icon: 'zap',
        title: 'Real-Time Competitive Intelligence',
        description: 'Know within minutes when competitors adjust pricing',
      },
      {
        icon: 'shield',
        title: 'Semantic Price Understanding',
        description: 'Distinguishes "bundled pricing" from "unit pricing" and "promotional" from "permanent" changes',
      },
      {
        icon: 'clock',
        title: 'Historical Tracking',
        description: 'See pricing trends and patterns to inform your strategy',
      },
    ],
    howItWorks: [
      {
        step: 1,
        title: 'Add Competitor Pricing Pages',
        description: 'Tell Torale which competitors and pricing tiers to monitor',
        example: '"Competitor X\'s Enterprise plan pricing"',
      },
      {
        step: 2,
        title: 'AI Monitors Semantic Changes',
        description: 'Torale ignores layout changes and focuses on meaningful price shifts',
        example: 'Detects "$99/mo" → "$79/mo" even if page redesigned',
      },
      {
        step: 3,
        title: 'Strategic Notifications',
        description: 'Get alerts with context: what changed, by how much, and competitive implications',
        example: '"Competitor reduced Enterprise plan by 20%, now $800 vs your $999"',
      },
    ],
    exampleConditions: [
      {
        title: 'Direct Competitor Watch',
        condition: 'Alert when Competitor X changes their Pro plan pricing',
        result: 'Matched their price drop within 2 hours, retained 3 at-risk customers',
      },
      {
        title: 'Market Positioning',
        condition: 'Notify if any competitor prices below our entry tier',
        result: 'Identified market trend toward aggressive pricing, adjusted strategy',
      },
      {
        title: 'Feature Parity Tracking',
        condition: 'Watch for new features added to competitors\' premium tiers',
        result: 'Proactively launched similar feature before sales objections increased',
      },
    ],
    faq: [
      {
        question: 'How does Torale handle complex pricing structures?',
        answer: 'Torale\'s AI understands tiered pricing, volume discounts, annual vs monthly billing, and promotional pricing. It can distinguish between a temporary sale and a permanent price change.',
      },
      {
        question: 'Will I get false alerts from page redesigns?',
        answer: 'No. Unlike visual diff tools that alert on every CSS change, Torale uses semantic understanding to detect only meaningful pricing changes.',
      },
      {
        question: 'Can I monitor competitors in different markets?',
        answer: 'Yes, Torale can monitor multiple competitors across different regions, understanding regional pricing variations and currency conversions.',
      },
      {
        question: 'How quickly do I get notified?',
        answer: 'Typically within 5-15 minutes of a pricing change, depending on your monitoring frequency settings.',
      },
    ],
    relatedUseCases: ['steam-game-price-alerts', 'api-deprecation-monitor'],
  },
  'crypto-exchange-listing-alert': {
    name: 'Crypto Exchange Listing Alerts',
    tagline: 'Catch the "Binance Effect" Pump',
    metaTitle: 'Crypto Exchange Listing Alert Tool - Binance, Coinbase - Torale',
    metaDescription: 'Get instant alerts when tokens are listed on Binance, Coinbase, or other major exchanges. Buy before the pump with AI-powered crypto monitoring.',
    heroTitle: 'The "Binance Effect" is Real. Catch the Pump.',
    heroSubtitle: 'Buy tokens moments before they hit major liquidity and skyrocket',
    targetKeyword: 'new coin binance listing alert',
    problemStatement: 'By the time you see a listing announcement on Twitter, the price has already pumped 50%. You need instant, verified alerts the moment exchange announcements go live.',
    solutionStatement: 'Torale monitors exchange announcement pages, official blogs, and trading pair additions using AI that understands the difference between "listing", "delisting", and "trading competition."',
    benefits: [
      {
        icon: 'zap',
        title: 'Seconds Matter',
        description: 'Get notified within 1-2 minutes of official announcement',
      },
      {
        icon: 'shield',
        title: 'Verified Sources Only',
        description: 'AI verifies listings from official exchange sources, avoiding rumors',
      },
      {
        icon: 'clock',
        title: 'Multi-Exchange Monitoring',
        description: 'Track Binance, Coinbase, Kraken, KuCoin, and 20+ exchanges simultaneously',
      },
    ],
    howItWorks: [
      {
        step: 1,
        title: 'Select Exchanges & Tokens',
        description: 'Monitor specific tokens or track all new listings across exchanges',
        example: '"Alert when [Token] lists on Binance or Coinbase"',
      },
      {
        step: 2,
        title: 'AI Monitors Announcements',
        description: 'Torale tracks official blogs, announcement pages, and trading pair additions',
        example: 'Distinguishes "spot listing" from "futures listing"',
      },
      {
        step: 3,
        title: 'Instant Buy Signal',
        description: 'Receive webhook to your trading bot or instant notification to buy manually',
        example: 'Buy before Twitter announcement spreads',
      },
    ],
    exampleConditions: [
      {
        title: 'Major Exchange Listing',
        condition: 'Alert when [Token] is announced for Binance or Coinbase listing',
        result: 'Bought 2 minutes before Twitter announcement, 40% gain in 1 hour',
      },
      {
        title: 'New Token Discovery',
        condition: 'Notify me of all new token listings on top 5 exchanges',
        result: 'Discovered early-stage projects before mainstream attention',
      },
      {
        title: 'Futures Listing Watch',
        condition: 'Track when tokens get futures/perpetual contracts added',
        result: 'Shorted overheated tokens that got futures listings',
      },
    ],
    faq: [
      {
        question: 'How fast are the alerts compared to Twitter?',
        answer: 'Torale monitors exchange websites directly and typically alerts 1-5 minutes before official Twitter announcements. This gives you time to execute before the crowd reaction.',
      },
      {
        question: 'Can this integrate with my trading bot?',
        answer: 'Yes, Torale supports webhooks that can trigger your trading bot instantly upon listing detection.',
      },
      {
        question: 'How do you avoid false positives?',
        answer: 'Torale\'s AI understands the difference between listing announcements, trading competitions, and other exchange news. It only alerts on actual spot or futures listings.',
      },
      {
        question: 'Which exchanges are supported?',
        answer: 'Binance, Coinbase, Kraken, KuCoin, OKX, Bybit, Gate.io, Huobi, and 15+ other major exchanges. We can add custom exchanges on request.',
      },
    ],
    relatedUseCases: ['steam-game-price-alerts', 'competitor-price-change-monitor'],
  },
};

const iconMap = {
  zap: Zap,
  shield: Shield,
  clock: Clock,
};

export function UseCasePage() {
  const { usecase } = useParams<{ usecase: string }>();
  const navigate = useNavigate();

  if (!usecase || !USE_CASES[usecase]) {
    return <Navigate to="/" replace />;
  }

  const data = USE_CASES[usecase];

  return (
    <>
      <Helmet>
        <title>{data.metaTitle}</title>
        <meta name="description" content={data.metaDescription} />
        <meta name="keywords" content={data.targetKeyword} />
        <link rel="canonical" href={`https://torale.ai/use-cases/${usecase}`} />
      </Helmet>

      <div className="min-h-screen bg-[#fafafa]">
        {/* Hero Section */}
        <section className="pt-32 pb-24 px-6 border-b border-zinc-200">
          <div className="container mx-auto max-w-6xl text-center">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mb-8"
            >
              <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border-2 border-zinc-900 text-zinc-900 text-xs font-mono font-bold uppercase tracking-wider shadow-brutalist">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                {data.tagline}
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="text-5xl md:text-6xl font-bold font-grotesk tracking-tight mb-6 text-zinc-900"
            >
              {data.heroTitle}
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="text-xl text-zinc-500 mb-10 max-w-2xl mx-auto font-medium"
            >
              {data.heroSubtitle}
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-4 justify-center"
            >
              <button
                onClick={() => navigate('/dashboard')}
                className="group inline-flex items-center justify-center gap-3 px-8 py-4 bg-brand-orange text-white text-lg font-bold hover:bg-[hsl(10,90%,50%)] transition-all shadow-brutalist-lg hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(24,24,27,1)] border-2 border-zinc-900"
              >
                Start Monitoring Free
                <ArrowRight className="h-5 w-5" />
              </button>
            </motion.div>
          </div>
        </section>

        {/* Problem/Solution Section */}
        <section className="py-16 px-4 bg-white">
          <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
            <div className="p-8 border-2 border-zinc-900 shadow-[4px_4px_0px_0px_rgba(239,68,68,0.3)]">
              <h3 className="text-2xl font-bold mb-4 text-red-600 font-['Space_Grotesk']">The Problem</h3>
              <p className="text-zinc-700 leading-relaxed">{data.problemStatement}</p>
            </div>
            <div className="p-8 border-2 border-zinc-900 shadow-[4px_4px_0px_0px_rgba(34,197,94,0.3)]">
              <h3 className="text-2xl font-bold mb-4 text-green-600 font-['Space_Grotesk']">The Solution</h3>
              <p className="text-zinc-700 leading-relaxed">{data.solutionStatement}</p>
            </div>
          </div>
        </section>

        {/* Benefits Section */}
        <section className="py-16 px-4 bg-zinc-50">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12 font-['Space_Grotesk']">Why Use Torale?</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {data.benefits.map((benefit, idx) => {
                const Icon = iconMap[benefit.icon];
                return (
                  <div
                    key={idx}
                    className="p-6 bg-white border-2 border-zinc-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]"
                  >
                    <Icon className="w-10 h-10 mb-4 text-yellow-400" strokeWidth={2} />
                    <h3 className="text-xl font-bold mb-2">{benefit.title}</h3>
                    <p className="text-zinc-600">{benefit.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section className="py-16 px-4 bg-white">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12 font-['Space_Grotesk']">How It Works</h2>
            <div className="space-y-6">
              {data.howItWorks.map((step, idx) => (
                <div
                  key={idx}
                  className="flex gap-6 p-6 border-2 border-zinc-900 bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]"
                >
                  <div className="flex-shrink-0 w-12 h-12 bg-yellow-400 border-2 border-zinc-900 flex items-center justify-center text-2xl font-bold">
                    {step.step}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-2">{step.title}</h3>
                    <p className="text-zinc-600 mb-2">{step.description}</p>
                    <code className="inline-block px-3 py-1 bg-zinc-100 border border-zinc-300 text-sm font-mono">
                      {step.example}
                    </code>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Example Conditions Section */}
        <section className="py-16 px-4 bg-zinc-50">
          <div className="max-w-5xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12 font-['Space_Grotesk']">Real-World Examples</h2>
            <div className="space-y-4">
              {data.exampleConditions.map((example, idx) => (
                <div
                  key={idx}
                  className="p-6 border-2 border-zinc-900 bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]"
                >
                  <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                    {example.title}
                  </h3>
                  <div className="pl-7 space-y-2">
                    <p className="text-zinc-700">
                      <span className="font-semibold">Condition:</span> {example.condition}
                    </p>
                    <p className="text-green-700">
                      <span className="font-semibold">Result:</span> {example.result}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="py-16 px-4 bg-white">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12 font-['Space_Grotesk']">Frequently Asked Questions</h2>
            <div className="space-y-6">
              {data.faq.map((item, idx) => (
                <div key={idx} className="border-b-2 border-zinc-200 pb-6 last:border-b-0">
                  <h3 className="text-xl font-bold mb-3">{item.question}</h3>
                  <p className="text-zinc-600 leading-relaxed">{item.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-16 px-4 bg-yellow-400 border-t-4 border-zinc-900">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-4xl font-bold mb-6 font-['Space_Grotesk']">
              Ready to Start Monitoring?
            </h2>
            <p className="text-xl mb-8 text-zinc-800">
              Join thousands using AI-powered monitoring to never miss important changes
            </p>
            <button
              onClick={() => navigate('/sign-up')}
              className="px-12 py-5 bg-zinc-900 text-white font-bold text-lg border-2 border-zinc-900 shadow-[6px_6px_0px_0px_rgba(0,0,0,0.3)] hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,0.3)] hover:translate-x-[-2px] hover:translate-y-[-2px] transition-all duration-150"
            >
              Start Free Trial →
            </button>
            <p className="mt-4 text-sm text-zinc-700">No credit card required • Free while in beta</p>
          </div>
        </section>
      </div>
    </>
  );
}
