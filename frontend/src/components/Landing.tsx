import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "@/lib/motion-compat";
import {
  ArrowRight,
  Terminal,
  Database,
  Zap,
  TrendingUp,
  FileText,
  Shield,
  Wifi,
  GitBranch,
  Globe,
} from "lucide-react";
import { UniversalEventStream } from "./ui/UniversalEventStream";
import { SystemTrace } from "./ui/SystemTrace";
import { TerminalSection } from "./ui/TerminalSection";
import { Logo } from "@/components/Logo";

/**
 * Landing Page - Based on MockLandingPage.tsx
 * Neo-brutalist design with "The Machine" philosophy
 */

// Background Pattern (Dotted)
const BackgroundPattern = () => (
  <div
    className="fixed inset-0 pointer-events-none z-0 opacity-[0.4]"
    style={{
      backgroundImage: `radial-gradient(#a1a1aa 1.5px, transparent 1.5px)`,
      backgroundSize: '24px 24px'
    }}
  />
);

// Badge Component
const Badge = ({ children }: { children: React.ReactNode }) => (
  <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border-2 border-zinc-900 text-zinc-900 text-xs font-mono font-bold uppercase tracking-wider shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]">
    {children}
  </div>
);

// Section Header
const SectionHeader = ({ title, subtitle, label }: { title: string; subtitle: string; label?: string }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    className="flex flex-col md:flex-row justify-between items-start md:items-end mb-16 border-b-2 border-zinc-100 pb-8"
  >
    <div className="max-w-2xl">
      <h2 className="text-4xl md:text-5xl font-bold font-grotesk tracking-tight mb-4 text-zinc-900">{title}</h2>
      <p className="text-zinc-500 text-lg font-light leading-relaxed max-w-xl">{subtitle}</p>
    </div>
    {label && <span className="font-mono text-sm font-bold text-zinc-300 mt-4 md:mt-0 tracking-widest uppercase">[{label}]</span>}
  </motion.div>
);

// Feature Card
const FeatureCard = ({ icon: Icon, title, desc, delay }: { icon: any; title: string; desc: string; delay: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.5, delay: delay * 0.1 }}
    className="bg-white p-8 border-2 border-transparent hover:border-zinc-900 hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] transition-all duration-200 group h-full"
  >
    <div className="mb-6 p-3 bg-zinc-50 inline-block rounded border border-zinc-100 group-hover:bg-zinc-900 group-hover:text-white transition-colors">
      <Icon className="h-6 w-6" strokeWidth={2} />
    </div>
    <h3 className="text-xl font-bold font-grotesk text-zinc-900 mb-3">{title}</h3>
    <p className="text-zinc-500 leading-relaxed text-sm">
      {desc}
    </p>
  </motion.div>
);

export default function Landing() {
  const navigate = useNavigate();
  const [availableSlots, setAvailableSlots] = useState<number | null>(null);

  useEffect(() => {
    // Fetch available user slots
    const fetchCapacity = async () => {
      try {
        const apiUrl = window.CONFIG?.apiUrl || import.meta.env.VITE_API_BASE_URL;
        const response = await fetch(`${apiUrl}/public/stats`);
        if (response.ok) {
          const data = await response.json();
          if (typeof data?.capacity?.available_slots === "number") {
            setAvailableSlots(data.capacity.available_slots);
          }
        }
      } catch (error) {
        if (import.meta.env.DEV) {
          console.error("Failed to fetch capacity:", error);
        }
      }
    };

    fetchCapacity();
  }, []);

  return (
    <>
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          "name": "Torale",
          "applicationCategory": "WebApplication",
          "operatingSystem": "Web",
          "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD"
          },
          "description": "Create monitoring tasks with natural language. Get notified when conditions are met using Google Search + LLM analysis."
        })}
      </script>
      <div className="min-h-screen bg-[#fafafa] text-zinc-900 font-sans selection:bg-[hsl(10,90%,55%)] selection:text-white">

        <BackgroundPattern />

      {/* Navigation */}
      <nav className="sticky top-0 z-50 w-full bg-[#fafafa]/90 backdrop-blur-md border-b border-zinc-200">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <button onClick={() => navigate('/')} className="cursor-pointer">
              <Logo />
            </button>

            <div className="hidden md:flex gap-8 text-sm font-medium text-zinc-500">
              <button onClick={() => navigate('/explore')} className="hover:text-black transition-colors">Explore</button>
              <a href="#use-cases" className="hover:text-black transition-colors">Use Cases</a>
              <a href="#pricing" className="hover:text-black transition-colors">Pricing</a>
              <button onClick={() => navigate('/changelog')} className="hover:text-black transition-colors">Changelog</button>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button onClick={() => navigate('/sign-in')} className="text-sm font-bold text-zinc-900 hover:underline px-3 py-2">Sign In</button>
            <button onClick={() => navigate('/dashboard')} className="bg-zinc-900 text-white px-5 py-2 text-sm font-bold hover:bg-[hsl(10,90%,55%)] transition-colors shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] active:translate-y-[2px] active:shadow-none">
              Start Monitoring
            </button>
          </div>
        </div>
      </nav>

      <main className="relative z-10">

        {/* Hero Section */}
        <section className="relative pt-32 pb-24 px-6 border-b border-zinc-200 overflow-hidden">
          <div className="container mx-auto max-w-6xl grid lg:grid-cols-2 gap-20 items-center relative z-10">

            {/* Left Content */}
            <div>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
              >
                <Badge>
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                  System: Nominal
                </Badge>
              </motion.div>

              <h1 className="text-6xl md:text-7xl font-bold font-grotesk tracking-tight mb-8 mt-8 leading-[0.95] text-zinc-900">
                Make the internet<br />
                <span className="text-zinc-400">work for you.</span>
              </h1>

              <p className="text-xl text-zinc-500 mb-10 max-w-lg font-medium leading-relaxed">
                Don't just browse the web—subscribe to it. Torale turns any website change into a notification, webhook, or structured data stream.
              </p>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.2, ease: "easeOut" }}
                className="flex flex-col sm:flex-row gap-4"
              >
                <button
                  onClick={() => navigate('/dashboard')}
                  className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-[hsl(10,90%,55%)] text-white text-lg font-bold hover:bg-[hsl(10,90%,50%)] transition-all shadow-[6px_6px_0px_0px_rgba(24,24,27,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(24,24,27,1)] border-2 border-zinc-900"
                >
                  Create Monitor
                  <ArrowRight className="h-5 w-5" />
                </button>

                <a
                  href="https://docs.torale.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group inline-flex items-center justify-center gap-2 px-8 py-4 bg-white hover:bg-zinc-50 transition-all font-bold text-zinc-900 border-2 border-zinc-200"
                >
                  <Terminal className="h-4 w-4 text-zinc-400 group-hover:text-black" />
                  Documentation
                </a>
              </motion.div>
            </div>

            {/* Right Content: Universal Feed */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1, delay: 0.2 }}
              className="relative hidden lg:block"
            >
              <UniversalEventStream />
            </motion.div>
          </div>
        </section>

        {/* Architecture Section (Sticky Scroll) */}
        <section className="bg-zinc-50 border-b border-zinc-200 pt-24">
          <div className="container mx-auto max-w-6xl px-6">
            <SectionHeader
              title="System Architecture"
              subtitle="We re-engineered the monitoring stack to eliminate flakiness."
              label="ARCHITECTURE"
            />

            <SystemTrace />
          </div>
        </section>

        {/* Use Cases Section */}
        <section id="use-cases" className="py-24 px-6 bg-white border-t border-zinc-200">
          <div className="container mx-auto max-w-6xl">
            <SectionHeader
              title="Monitor Anything"
              subtitle="If it's on the open web, Torale can track it."
              label="USE_CASES"
            />

            <div className="grid md:grid-cols-3 gap-8">

              {/* Use Case 1: Steam Game Price Alerts */}
              <Link to="/use-cases/steam-game-price-alerts" className="block">
                <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-all shadow-sm hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] group h-full flex flex-col">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="p-3 bg-blue-50 text-blue-600 rounded-lg border border-blue-100 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                      <TrendingUp className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold font-grotesk text-zinc-900">Steam Game Prices</h3>
                      <span className="font-mono text-xs text-zinc-400">#gaming #deals</span>
                    </div>
                  </div>
                  <p className="text-zinc-600 mb-6 font-medium flex-grow">
                    "Alert me when Elden Ring drops below $30 on Steam"
                  </p>
                  <div className="bg-zinc-50 p-4 border border-zinc-200 font-mono text-xs text-zinc-500 rounded-sm group-hover:border-zinc-400 transition-colors">
                    &gt; Price detected: $29.99<br />
                    &gt; Target met: <span className="text-green-600 font-bold">ALERT SENT</span>
                  </div>
                  <div className="mt-4 flex items-center gap-2 text-zinc-900 font-bold text-sm group-hover:text-[hsl(10,90%,55%)] transition-colors">
                    Learn More <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </Link>

              {/* Use Case 2: Competitor Price Monitoring */}
              <Link to="/use-cases/competitor-price-change-monitor" className="block">
                <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-all shadow-sm hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] group h-full flex flex-col">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="p-3 bg-purple-50 text-purple-600 rounded-lg border border-purple-100 group-hover:bg-purple-600 group-hover:text-white transition-colors">
                      <Shield className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold font-grotesk text-zinc-900">Competitor Pricing</h3>
                      <span className="font-mono text-xs text-zinc-400">#saas #intel</span>
                    </div>
                  </div>
                  <p className="text-zinc-600 mb-6 font-medium flex-grow">
                    "Watch top 3 competitors. Alert if they change Enterprise tier pricing."
                  </p>
                  <div className="bg-zinc-50 p-4 border border-zinc-200 font-mono text-xs text-zinc-500 rounded-sm group-hover:border-zinc-400 transition-colors">
                    &gt; Competitor X pricing change<br />
                    &gt; <span className="text-red-600">$999/mo</span> → <span className="text-amber-600 font-bold">$800/mo</span>
                  </div>
                  <div className="mt-4 flex items-center gap-2 text-zinc-900 font-bold text-sm group-hover:text-[hsl(10,90%,55%)] transition-colors">
                    Learn More <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </Link>

              {/* Use Case 3: Crypto Exchange Listings */}
              <Link to="/use-cases/crypto-exchange-listing-alert" className="block">
                <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-all shadow-sm hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] group h-full flex flex-col">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg border border-emerald-100 group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                      <Zap className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold font-grotesk text-zinc-900">Crypto Listings</h3>
                      <span className="font-mono text-xs text-zinc-400">#crypto #trading</span>
                    </div>
                  </div>
                  <p className="text-zinc-600 mb-6 font-medium flex-grow">
                    "Alert when [TOKEN] is listed on Binance or Coinbase"
                  </p>
                  <div className="bg-zinc-50 p-4 border border-zinc-200 font-mono text-xs text-zinc-500 rounded-sm group-hover:border-zinc-400 transition-colors">
                    &gt; New listing detected<br />
                    &gt; Exchange: <span className="text-amber-600 font-bold">BINANCE SPOT</span>
                  </div>
                  <div className="mt-4 flex items-center gap-2 text-zinc-900 font-bold text-sm group-hover:text-[hsl(10,90%,55%)] transition-colors">
                    Learn More <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </Link>

            </div>
          </div>
        </section>

        {/* Comparison Section */}
        <section className="py-24 px-6 bg-zinc-50 border-t border-zinc-200">
          <div className="container mx-auto max-w-6xl">
            <SectionHeader
              title="Compare Torale"
              subtitle="See how we stack up against traditional monitoring tools"
              label="ALTERNATIVES"
            />

            <div className="grid md:grid-cols-3 gap-8">

              {/* vs VisualPing */}
              <Link to="/compare/visualping-alternative" className="block">
                <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-all shadow-sm hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] group h-full flex flex-col">
                  <h3 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">vs VisualPing</h3>
                  <p className="text-zinc-600 mb-6 flex-grow">
                    AI semantic monitoring vs pixel diffs. Get notified about meaningful changes, not CSS updates.
                  </p>
                  <div className="flex items-center gap-2 text-zinc-900 font-bold group-hover:text-[hsl(10,90%,55%)] transition-colors">
                    Compare <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </Link>

              {/* vs Distill */}
              <Link to="/compare/distill-alternative" className="block">
                <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-all shadow-sm hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] group h-full flex flex-col">
                  <h3 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">vs Distill</h3>
                  <p className="text-zinc-600 mb-6 flex-grow">
                    Natural language conditions vs XPath selectors. Monitor what matters without regex hell.
                  </p>
                  <div className="flex items-center gap-2 text-zinc-900 font-bold group-hover:text-[hsl(10,90%,55%)] transition-colors">
                    Compare <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </Link>

              {/* vs ChangeTower */}
              <Link to="/compare/changetower-alternative" className="block">
                <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-all shadow-sm hover:shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] group h-full flex flex-col">
                  <h3 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4">vs ChangeTower</h3>
                  <p className="text-zinc-600 mb-6 flex-grow">
                    Conditional alerts vs basic notifications. Set precise triggers, not just "something changed".
                  </p>
                  <div className="flex items-center gap-2 text-zinc-900 font-bold group-hover:text-[hsl(10,90%,55%)] transition-colors">
                    Compare <ArrowRight className="w-4 h-4" />
                  </div>
                </div>
              </Link>

            </div>
          </div>
        </section>

        {/* Developer Experience Section */}
        <section className="bg-zinc-50 border-b border-zinc-200 py-24 px-6">
          <div className="container mx-auto max-w-6xl">
            <div className="flex flex-col lg:flex-row gap-16 items-center">
              <div className="lg:w-1/2 order-2 lg:order-1">
                <TerminalSection />
              </div>

              <div className="lg:w-1/2 order-1 lg:order-2">
                <SectionHeader
                  title="You live in the terminal. So do we."
                  subtitle="Torale is API-first and CLI-native. Script your monitoring infrastructure alongside your code."
                  label="DX_FOCUSED"
                />

                <ul className="space-y-6 mt-8">
                  <li className="flex items-start gap-4">
                    <div className="p-2 bg-white rounded border border-zinc-200 text-zinc-600"><Terminal className="w-5 h-5" /></div>
                    <div>
                      <h4 className="font-bold text-zinc-900 text-lg font-grotesk">Full CLI Control</h4>
                      <p className="text-zinc-500 text-sm">Create, list, and debug monitors without leaving your shell.</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-4">
                    <div className="p-2 bg-white rounded border border-zinc-200 text-zinc-600"><Database className="w-5 h-5" /></div>
                    <div>
                      <h4 className="font-bold text-zinc-900 text-lg font-grotesk">Structured JSON</h4>
                      <p className="text-zinc-500 text-sm">We don't send you raw HTML. You get clean, typed JSON objects.</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-4">
                    <div className="p-2 bg-white rounded border border-zinc-200 text-zinc-600"><Zap className="w-5 h-5" /></div>
                    <div>
                      <h4 className="font-bold text-zinc-900 text-lg font-grotesk">Instant Webhooks</h4>
                      <p className="text-zinc-500 text-sm">Pipe events directly into Slack, Discord, or your own backend.</p>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-24 px-6 bg-white border-t border-zinc-200">
          <div className="container mx-auto max-w-4xl text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="space-y-8"
            >
              <div>
                <h2 className="text-4xl md:text-5xl font-bold font-grotesk tracking-tight mb-4 text-zinc-900">
                  Simple Pricing
                </h2>
                <p className="text-xl text-zinc-500 max-w-2xl mx-auto">
                  No credit card required. Start monitoring in seconds.
                </p>
              </div>

              <div className="bg-white p-12 border-2 border-zinc-900 shadow-brutalist-lg max-w-lg mx-auto">
                <div className="mb-6">
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 border-2 border-emerald-500 text-emerald-700 text-xs font-mono font-bold uppercase tracking-wider mb-4">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                    Beta Access
                  </div>
                  <div className="text-6xl font-bold font-grotesk text-zinc-900 mb-2">
                    $0
                  </div>
                  <p className="text-zinc-500 font-mono text-sm">
                    {availableSlots !== null
                      ? `Free for ${availableSlots} remaining user${availableSlots === 1 ? '' : 's'}`
                      : 'Free while in beta'}
                  </p>
                </div>

                <div className="space-y-3 text-left mb-8">
                  <div className="flex items-center gap-2 text-zinc-600">
                    <div className="w-5 h-5 bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 font-bold text-xs">✓</div>
                    <span className="text-sm">Unlimited monitors</span>
                  </div>
                  <div className="flex items-center gap-2 text-zinc-600">
                    <div className="w-5 h-5 bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 font-bold text-xs">✓</div>
                    <span className="text-sm">AI-powered search monitoring</span>
                  </div>
                  <div className="flex items-center gap-2 text-zinc-600">
                    <div className="w-5 h-5 bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 font-bold text-xs">✓</div>
                    <span className="text-sm">In-app notifications</span>
                  </div>
                  <div className="flex items-center gap-2 text-zinc-600">
                    <div className="w-5 h-5 bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 font-bold text-xs">✓</div>
                    <span className="text-sm">Full API access</span>
                  </div>
                </div>

                <button
                  onClick={() => navigate('/dashboard')}
                  className="w-full bg-zinc-900 text-white px-8 py-4 text-lg font-bold hover:bg-[hsl(10,90%,55%)] transition-colors shadow-brutalist active:translate-y-[2px] active:shadow-none"
                >
                  Start Monitoring
                </button>

                <p className="text-xs text-zinc-400 mt-4 font-mono">
                  No credit card required • Free while in beta
                </p>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-zinc-950 text-zinc-400 border-t border-zinc-900 pt-20 pb-10 px-6">
          <div className="container mx-auto max-w-6xl">
            <div className="grid md:grid-cols-6 gap-8 mb-16">
              <div className="col-span-2">
                <span className="font-bold text-xl tracking-tight block mb-6 text-white font-grotesk">τorale</span>
                <p className="text-zinc-500 text-sm leading-relaxed">
                  Reliable, intelligent monitoring for the modern stack.
                </p>
              </div>

              <div>
                <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Product</h4>
                <ul className="space-y-3 text-sm text-zinc-500 font-medium">
                  <li><a href="#use-cases" className="hover:text-white transition-colors">Use Cases</a></li>
                  <li><button onClick={() => navigate('/changelog')} className="hover:text-white transition-colors">Changelog</button></li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Solutions</h4>
                <ul className="space-y-3 text-sm text-zinc-500 font-medium">
                  <li><Link to="/use-cases/steam-game-price-alerts" className="hover:text-white transition-colors">Gaming Deals</Link></li>
                  <li><Link to="/use-cases/competitor-price-change-monitor" className="hover:text-white transition-colors">Price Monitoring</Link></li>
                  <li><Link to="/use-cases/crypto-exchange-listing-alert" className="hover:text-white transition-colors">Crypto Alerts</Link></li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Compare</h4>
                <ul className="space-y-3 text-sm text-zinc-500 font-medium">
                  <li><Link to="/compare/visualping-alternative" className="hover:text-white transition-colors">vs VisualPing</Link></li>
                  <li><Link to="/compare/distill-alternative" className="hover:text-white transition-colors">vs Distill</Link></li>
                  <li><Link to="/compare/changetower-alternative" className="hover:text-white transition-colors">vs ChangeTower</Link></li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Resources</h4>
                <ul className="space-y-3 text-sm text-zinc-500 font-medium">
                  <li><a href="https://docs.torale.ai" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Documentation</a></li>
                  <li><a href="https://api.torale.ai/redoc" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">API Reference</a></li>
                  <li><a href="https://torale.openstatus.dev" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Status</a></li>
                  <li><a href="https://github.com/prassanna-ravishankar/torale" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub</a></li>
                </ul>
              </div>
            </div>

            <div className="border-t border-zinc-900 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="flex flex-col md:flex-row items-center gap-4">
                <div className="text-xs text-zinc-600 font-mono">
                  [ © 2025 TORALE LABS INC. ]
                </div>
                <div className="flex gap-4 text-xs text-zinc-500">
                  <Link to="/terms" className="hover:text-white transition-colors">Terms of Service</Link>
                  <span className="text-zinc-700">•</span>
                  <Link to="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
                </div>
              </div>
              <div className="flex gap-6">
                <a href="https://github.com/prassanna-ravishankar/torale" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
                  <GitBranch className="w-5 h-5 text-zinc-500 hover:text-white cursor-pointer transition-colors" />
                </a>
                <a href="https://torale.openstatus.dev" target="_blank" rel="noopener noreferrer" aria-label="Status">
                  <Globe className="w-5 h-5 text-zinc-500 hover:text-white cursor-pointer transition-colors" />
                </a>
              </div>
            </div>
          </div>
        </footer>

      </main>
    </div>
    </>
  );
}
