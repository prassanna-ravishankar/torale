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
import { ParticleNetwork } from "./ui/ParticleNetwork";
import { UniversalEventStream } from "./ui/UniversalEventStream";
import { SystemTrace } from "./ui/SystemTrace";
import { TerminalSection } from "./ui/TerminalSection";
import { Logo } from "@/components/Logo";

/**
 * Landing Page - Based on MockLandingPage.tsx
 * Neo-brutalist design with "The Machine" philosophy
 */

// Font Loader (inline style injection matching mock)
const FontLoader = () => (
  <style dangerouslySetInnerHTML={{
    __html: `
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    .font-grotesk { font-family: 'Space Grotesk', sans-serif; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
  `}} />
);

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
  const [mounted, setMounted] = useState(false);
  const [availableSlots, setAvailableSlots] = useState<number | null>(null);

  useEffect(() => {
    setMounted(true);

    // Fetch available user slots
    const fetchCapacity = async () => {
      try {
        // Use relative URL - Vite proxy will handle it in dev, production uses full URL
        const response = await fetch('/public/stats');
        if (response.ok) {
          const data = await response.json();
          if (typeof data?.capacity?.available_slots === "number") {
            setAvailableSlots(data.capacity.available_slots);
          }
        }
      } catch (error) {
        console.error("Failed to fetch capacity:", error);
      }
    };

    fetchCapacity();
  }, []);

  return (
    <div className={`min-h-screen bg-[#fafafa] text-zinc-900 font-sans selection:bg-[hsl(10,90%,55%)] selection:text-white transition-opacity duration-500 ${mounted ? 'opacity-100' : 'opacity-0'}`}>

      <FontLoader />
      <BackgroundPattern />

      {/* Navigation */}
      <nav className="sticky top-0 z-50 w-full bg-[#fafafa]/90 backdrop-blur-md border-b border-zinc-200">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <button onClick={() => navigate('/')} className="cursor-pointer">
              <Logo />
            </button>

            <div className="hidden md:flex gap-8 text-sm font-medium text-zinc-500">
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
          <ParticleNetwork />

          <div className="container mx-auto max-w-6xl grid lg:grid-cols-2 gap-20 items-center relative z-10">

            {/* Left Content */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, ease: "easeOut" }}
            >
              <Badge>
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                System: Nominal
              </Badge>

              <h1 className="text-6xl md:text-7xl font-bold font-grotesk tracking-tight mb-8 mt-8 leading-[0.95] text-zinc-900">
                Make the internet<br />
                <span className="text-zinc-400">work for you.</span>
              </h1>

              <p className="text-xl text-zinc-500 mb-10 max-w-lg font-medium leading-relaxed">
                Don't just browse the web—subscribe to it. Torale turns any website change into a notification, webhook, or structured data stream.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
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
              </div>
            </motion.div>

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

            <div className="grid lg:grid-cols-2 gap-8">

              {/* Use Case 1 */}
              <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-colors shadow-sm group">
                <div className="flex items-center gap-4 mb-6">
                  <div className="p-3 bg-blue-50 text-blue-600 rounded-lg border border-blue-100">
                    <TrendingUp className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold font-grotesk text-zinc-900">Market Intelligence</h3>
                    <span className="font-mono text-xs text-zinc-400">#pricing #competitors</span>
                  </div>
                </div>
                <p className="text-zinc-600 mb-6 font-medium">
                  "Watch our top 3 competitors. Alert me if they change the price of their Enterprise tier or remove 'SSO' from the features list."
                </p>
                <div className="bg-zinc-50 p-4 border border-zinc-200 font-mono text-xs text-zinc-500 rounded-sm group-hover:border-zinc-400 transition-colors">
                  &gt; Detected change on /pricing<br />
                  &gt; <span className="text-red-600 line-through">$49/mo</span> &rarr; <span className="text-green-600">$59/mo</span>
                </div>
              </div>

              {/* Use Case 2 */}
              <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-colors shadow-sm group">
                <div className="flex items-center gap-4 mb-6">
                  <div className="p-3 bg-purple-50 text-purple-600 rounded-lg border border-purple-100">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold font-grotesk text-zinc-900">Regulatory Watch</h3>
                    <span className="font-mono text-xs text-zinc-400">#compliance #legal</span>
                  </div>
                </div>
                <p className="text-zinc-600 mb-6 font-medium">
                  "Monitor the EU AI Act official journal. Notify legal if new amendments regarding 'General Purpose AI' are published."
                </p>
                <div className="bg-zinc-50 p-4 border border-zinc-200 font-mono text-xs text-zinc-500 rounded-sm group-hover:border-zinc-400 transition-colors">
                  &gt; New document found: "Amendment 45b"<br />
                  &gt; Context match: "High Risk AI Systems"
                </div>
              </div>

              {/* Use Case 3 */}
              <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-colors shadow-sm group">
                <div className="flex items-center gap-4 mb-6">
                  <div className="p-3 bg-red-50 text-red-600 rounded-lg border border-red-100">
                    <Shield className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold font-grotesk text-zinc-900">Security Ops</h3>
                    <span className="font-mono text-xs text-zinc-400">#cve #vulnerabilities</span>
                  </div>
                </div>
                <p className="text-zinc-600 mb-6 font-medium">
                  "Poll the NVD feed every minute. Page the on-call engineer if a critical CVE is found for 'Log4j' or 'OpenSSL'."
                </p>
                <div className="bg-zinc-50 p-4 border border-zinc-200 font-mono text-xs text-zinc-500 rounded-sm group-hover:border-zinc-400 transition-colors">
                  &gt; CVE-2025-9921 Detected<br />
                  &gt; Severity: <span className="text-red-600 font-bold">CRITICAL (9.8)</span>
                </div>
              </div>

              {/* Use Case 4 */}
              <div className="bg-white p-8 border-2 border-zinc-100 hover:border-zinc-900 transition-colors shadow-sm group">
                <div className="flex items-center gap-4 mb-6">
                  <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg border border-emerald-100">
                    <Wifi className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold font-grotesk text-zinc-900">Inventory & Status</h3>
                    <span className="font-mono text-xs text-zinc-400">#infrastructure #supply</span>
                  </div>
                </div>
                <p className="text-zinc-600 mb-6 font-medium">
                  "Check the AWS Health Dashboard. Trigger our internal incident response if 'us-east-1' reports degradation."
                </p>
                <div className="bg-zinc-50 p-4 border border-zinc-200 font-mono text-xs text-zinc-500 rounded-sm group-hover:border-zinc-400 transition-colors">
                  &gt; Service: EC2 (us-east-1)<br />
                  &gt; Status: <span className="text-amber-600 font-bold">DEGRADED</span>
                </div>
              </div>

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
            <div className="grid md:grid-cols-4 gap-12 mb-16">
              <div className="col-span-1 md:col-span-1">
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
                <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Developers</h4>
                <ul className="space-y-3 text-sm text-zinc-500 font-medium">
                  <li><a href="https://docs.torale.ai" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Documentation</a></li>
                  <li><a href="https://api.torale.ai/redoc" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">API Reference</a></li>
                  <li><a href="https://torale.openstatus.dev" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Status</a></li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Community</h4>
                <ul className="space-y-3 text-sm text-zinc-500 font-medium">
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
  );
}
