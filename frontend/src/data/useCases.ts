/**
 * Use case data for SEO landing pages
 * Used by UseCasePage.tsx
 */

export interface UseCaseData {
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

export const USE_CASES: Record<string, UseCaseData> = {
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
