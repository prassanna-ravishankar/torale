import React, { useState, useEffect, useRef } from "react";
import { motion, useScroll, AnimatePresence } from "framer-motion";
import { 
  Search, 
  ArrowRight, 
  Terminal, 
  Activity, 
  CheckCircle2, 
  Clock, 
  Globe, 
  Shield, 
  Zap, 
  Database,
  Cpu,
  GitBranch,
  BellRing,
  FileText,
  AlertTriangle,
  TrendingUp,
  Box,
  Eye,
  Lock,
  Wifi,
  ShoppingBag,
  Newspaper,
  Gavel
} from "lucide-react";

// --- Font Injection ---
const FontLoader = () => (
  <style dangerouslySetInnerHTML={{__html: `
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    .font-grotesk { font-family: 'Space Grotesk', sans-serif; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
  `}} />
);

// --- Background Pattern (Dotted) ---
const BackgroundPattern = () => (
  <div 
    className="fixed inset-0 pointer-events-none z-0 opacity-[0.4]"
    style={{
      backgroundImage: `radial-gradient(#a1a1aa 1.5px, transparent 1.5px)`,
      backgroundSize: '24px 24px'
    }}
  />
);

// --- Hero Visual: Universal Event Stream ---
const UniversalEventStream = () => {
  const [events, setEvents] = useState([
    { id: 1, icon: ShoppingBag, title: "Tesla Model Y", diff: "$44,990 -> $42,990", source: "tesla.com", color: "text-blue-600", bg: "bg-blue-50" },
    { id: 2, icon: Gavel, title: "EU AI Act Update", diff: "New Article 45b added", source: "eur-lex.europa.eu", color: "text-purple-600", bg: "bg-purple-50" },
    { id: 3, icon: AlertTriangle, title: "CVE-2025-921", diff: "Severity: Critical (9.8)", source: "nvd.nist.gov", color: "text-red-600", bg: "bg-red-50" },
  ]);

  useEffect(() => {
    const stream = [
      { icon: Newspaper, title: "HackerNews", diff: "Post > 500 pts: 'AGI achieved'", source: "news.ycombinator.com", color: "text-orange-600", bg: "bg-orange-50" },
      { icon: TrendingUp, title: "AAPL 10-K Filing", diff: "Keyword: 'Acquisition'", source: "sec.gov/edgar", color: "text-emerald-600", bg: "bg-emerald-50" },
      { icon: Globe, title: "Reddit /r/sysadmin", diff: "Keyword: 'AWS Outage'", source: "reddit.com", color: "text-indigo-600", bg: "bg-indigo-50" },
      { icon: ShoppingBag, title: "BestBuy Restock", diff: "Status: In Stock", source: "bestbuy.com", color: "text-blue-600", bg: "bg-blue-50" },
    ];
    
    let index = 0;
    const interval = setInterval(() => {
      const newEvent = { ...stream[index], id: Date.now() };
      setEvents(prev => [newEvent, ...prev].slice(0, 4));
      index = (index + 1) % stream.length;
    }, 2200);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-full max-w-md mx-auto perspective-1000">
      <div className="absolute inset-0 bg-zinc-100 rounded-xl transform rotate-3 scale-105 opacity-50 blur-sm"></div>
      
      <div className="bg-white border-2 border-zinc-100 rounded-xl shadow-2xl overflow-hidden relative z-10 flex flex-col h-[380px]">
        <div className="bg-white border-b border-zinc-100 px-5 py-4 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-[hsl(10,90%,55%)] animate-pulse"></div>
            <span className="text-xs font-grotesk font-bold text-zinc-900 tracking-wider uppercase">Incoming Signals</span>
          </div>
          <span className="text-[10px] text-zinc-400 font-mono">Stream: Active</span>
        </div>
        
        <div className="p-4 flex-1 overflow-hidden relative bg-zinc-50/30">
          <div className="absolute inset-0 bg-gradient-to-b from-white/0 via-white/0 to-white pointer-events-none z-20"></div>
          
          <div className="space-y-3">
            <AnimatePresence initial={false}>
              {events.map((event) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, y: -30, scale: 0.9 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 30, scale: 0.95 }}
                  transition={{ type: "spring", stiffness: 300, damping: 25 }}
                  className="bg-white p-3 rounded-lg border border-zinc-200 shadow-sm flex items-start gap-3 group hover:border-zinc-400 transition-colors"
                >
                  <div className={`p-2 rounded-md ${event.bg} ${event.color} shrink-0`}>
                    <event.icon className="w-5 h-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex justify-between items-start">
                      <h4 className="text-sm font-bold text-zinc-900 truncate">{event.title}</h4>
                      <span className="text-[10px] text-zinc-400 font-mono">{event.source}</span>
                    </div>
                    <div className="text-xs font-mono text-zinc-600 mt-1 bg-zinc-50 px-2 py-1 rounded border border-zinc-100 truncate">
                      {'>'} {event.diff}
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- Components ---

const Badge = ({ children }) => (
  <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border-2 border-zinc-900 text-zinc-900 text-xs font-mono font-bold uppercase tracking-wider shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]">
    {children}
  </div>
);

const SectionHeader = ({ title, subtitle, label }) => (
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

const FeatureCard = ({ icon: Icon, title, desc, delay }) => (
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

// --- Scroll System Trace (Restyled) ---

const TerminalLog = ({ activeStep }) => {
  const steps = [
    { id: 1, cmd: "CRON_WAKE", msg: "Triggering scheduled job 0x81" },
    { id: 1, cmd: "ALLOC", msg: "Worker node assigned (us-east)" },
    { id: 2, cmd: "HTTP_GET", msg: "Target: competitor.com/pricing" },
    { id: 2, cmd: "DOM_PARSE", msg: "Structuring HTML content..." },
    { id: 3, cmd: "LLM_CTX", msg: "Injecting schema to context window" },
    { id: 3, cmd: "INFERENCE", msg: "Analyzing diff... Match found." },
    { id: 4, cmd: "STATE", msg: "Writing to persistent log" },
    { id: 4, cmd: "NOTIFY", msg: "Webhook dispatched (200 OK)" }
  ];

  const visibleSteps = activeStep === 1 ? 2 : activeStep === 2 ? 4 : activeStep === 3 ? 6 : 8;

  return (
    <div className="font-mono text-xs space-y-3">
      {steps.slice(0, visibleSteps).map((log, i) => (
        <motion.div 
          key={i} 
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex gap-4 border-b border-zinc-800/50 pb-2"
        >
          <span className="text-zinc-500 w-20 shrink-0">{log.cmd}</span>
          <span className={`
            ${i >= visibleSteps - 2 ? 'text-[hsl(10,90%,55%)]' : 'text-zinc-300'}
          `}>{log.msg}</span>
        </motion.div>
      ))}
      <div className="animate-pulse w-3 h-5 bg-[hsl(10,90%,55%)]" />
    </div>
  );
};

const SystemTrace = () => {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  const [activeStep, setActiveStep] = useState(1);

  useEffect(() => {
    return scrollYProgress.onChange((latest) => {
      if (latest < 0.2) setActiveStep(1);
      else if (latest < 0.5) setActiveStep(2);
      else if (latest < 0.8) setActiveStep(3);
      else setActiveStep(4);
    });
  }, [scrollYProgress]);

  const steps = [
    {
      id: 1,
      title: "Reliable Orchestration",
      description: "The machine starts here. Our distributed scheduler wakes up your agent exactly on time, every time. Guaranteed execution even if servers fail.",
      icon: Clock,
      detail: "Frequency: 5min"
    },
    {
      id: 2,
      title: "Anti-Detect Browsing",
      description: "We don't just 'curl'. We spin up headless browsers with sophisticated fingerprint rotation to view the web exactly like a human user.",
      icon: Eye,
      detail: "Mode: Stealth"
    },
    {
      id: 3,
      title: "Cognitive Processing",
      description: "The raw HTML is noisy. We pass it through a reasoning engine that 'reads' the page and answers your specific questions (e.g., 'Is it in stock?').",
      icon: Cpu,
      detail: "Reasoning: Enabled"
    },
    {
      id: 4,
      title: "Stateful Action",
      description: "Torale remembers the past. We only alert you when the answer *changes* (e.g., 'Out of Stock' -> 'In Stock'), reducing notification fatigue.",
      icon: Zap,
      detail: "Diff: Detected"
    }
  ];

  return (
    <div ref={containerRef} className="relative">
      <div className="md:grid md:grid-cols-2 md:gap-12 lg:gap-24">
        
        {/* Sticky Visualization */}
        <div className="hidden md:block relative h-full">
          <div className="sticky top-32 h-[500px] w-full bg-zinc-950 border-2 border-zinc-900 rounded-lg overflow-hidden shadow-2xl z-20 flex flex-col">
            <div className="h-12 border-b border-zinc-800 bg-zinc-900 flex items-center px-4 justify-between">
              <span className="font-mono text-xs text-zinc-400 font-bold uppercase tracking-widest">
                Kernel_Trace_v4
              </span>
              <div className="flex gap-2">
                <div className="w-3 h-3 bg-zinc-800 rounded-sm" />
                <div className="w-3 h-3 bg-zinc-800 rounded-sm" />
              </div>
            </div>
            
            <div className="flex-1 p-6 font-mono text-sm text-zinc-300 overflow-hidden relative">
              {/* Scanlines */}
              <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 pointer-events-none bg-[length:100%_4px,3px_100%] pointer-events-none" />
              
              <TerminalLog activeStep={activeStep} />
            </div>

            {/* Active Step Indicator */}
            <div className="h-2 bg-zinc-900 w-full flex">
              {[1,2,3,4].map(s => (
                <div key={s} className={`flex-1 transition-colors duration-300 ${s <= activeStep ? 'bg-[hsl(10,90%,55%)]' : 'bg-zinc-800'}`} />
              ))}
            </div>
          </div>
        </div>

        {/* Narrative Steps */}
        <div className="relative flex flex-col gap-[40vh] md:py-[5vh] pb-[20vh]">
          {steps.map((step) => (
            <motion.div 
              key={step.id}
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ margin: "-20% 0px -20% 0px" }}
              className="bg-white p-8 border-l-4 border-zinc-200 hover:border-[hsl(10,90%,55%)] transition-colors pl-8"
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="font-mono text-3xl font-bold text-zinc-200">0{step.id}</div>
                <div className="p-2 bg-zinc-100 rounded text-zinc-900"><step.icon className="w-5 h-5" /></div>
              </div>
              
              <h3 className="text-2xl font-bold font-grotesk mb-4 text-zinc-900">{step.title}</h3>
              <p className="text-zinc-500 leading-relaxed text-base mb-6 font-medium">
                {step.description}
              </p>
              
              <div className="inline-block bg-zinc-900 text-white text-xs font-mono px-3 py-1.5 rounded-sm">
                &gt; {step.detail}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

// --- Terminal Component (Developer Experience) ---
const TerminalSection = () => {
  return (
    <div className="w-full bg-zinc-950 rounded-xl overflow-hidden border border-zinc-800 shadow-2xl font-mono text-sm">
      <div className="bg-zinc-900 px-4 py-2 flex items-center gap-2 border-b border-zinc-800">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
          <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
        </div>
        <div className="ml-auto text-zinc-600 text-xs">user@dev:~/monitors</div>
      </div>
      
      <div className="p-8 text-zinc-300 space-y-6">
        <div>
          <div className="flex gap-2 mb-2">
            <span className="text-[hsl(10,90%,55%)]">➜</span>
            <span className="text-zinc-500">~</span>
            <span>pip install torale</span>
          </div>
          <div className="text-zinc-500 pl-6 text-xs">
            Successfully installed torale-2.0.0
          </div>
        </div>

        <div>
          <div className="flex gap-2 mb-2">
            <span className="text-[hsl(10,90%,55%)]">➜</span>
            <span className="text-zinc-500">~/monitors</span>
            <span>torale create "Competitor Pricing" \</span>
          </div>
          <div className="pl-6 border-l-2 border-zinc-800 ml-1">
            <div className="flex gap-2">
              <span className="text-purple-400">--url</span>
              <span className="text-green-400">"https://competitor.com/pricing"</span>
              <span>\</span>
            </div>
            <div className="flex gap-2">
              <span className="text-purple-400">--extract</span>
              <span className="text-green-400">"enterprise_tier_cost"</span>
              <span>\</span>
            </div>
            <div className="flex gap-2">
              <span className="text-purple-400">--alert-on</span>
              <span className="text-green-400">"change"</span>
            </div>
          </div>
        </div>

        <div className="pl-6 pt-2">
          <div className="text-[hsl(10,90%,55%)] flex items-center gap-2 mb-1">
            <CheckCircle2 className="w-4 h-4" />
            <span>Monitor deployed successfully</span>
          </div>
          <div className="text-zinc-600 text-xs">ID: mon_8e92f-22a1</div>
          <div className="text-zinc-600 text-xs">Status: Active (5min interval)</div>
        </div>

        <div className="flex gap-2">
          <span className="text-[hsl(10,90%,55%)]">➜</span>
          <span className="text-zinc-500">~/monitors</span>
          <span className="w-2 h-5 bg-zinc-500 animate-pulse block"></span>
        </div>
      </div>
    </div>
  );
};

// --- Clean Constellation Particle Network (Restored) ---
const ParticleNetwork = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = window.innerWidth;
    let height = window.innerHeight;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };
    window.addEventListener('resize', resize);
    resize();

    const particleCount = Math.min(width / 25, 60); 
    const particles: Array<{x: number, y: number, vx: number, vy: number}> = [];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.2,
        vy: (Math.random() - 0.5) * 0.2
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, width, height);
      
      particles.forEach((p, i) => {
        p.x += p.vx;
        p.y += p.vy;

        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < 180) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(0, 0, 0, ${0.08 * (1 - dist / 180)})`; 
            ctx.lineWidth = 1;
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.strokeStyle = 'rgba(0,0,0,0.1)';
        ctx.stroke();
      });

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas 
      ref={canvasRef} 
      className="absolute inset-0 pointer-events-none z-0"
    />
  );
};

// --- Main App Component ---

export default function App() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className={`min-h-screen bg-[#fafafa] text-zinc-900 font-sans selection:bg-[hsl(10,90%,55%)] selection:text-white transition-opacity duration-500 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
      
      <FontLoader />
      <BackgroundPattern />

      {/* --- Navigation --- */}
      <nav className="sticky top-0 z-50 w-full bg-[#fafafa]/90 backdrop-blur-md border-b border-zinc-200">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <a href="#" className="flex items-center gap-2 group">
              <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center rounded-sm font-grotesk font-bold text-lg group-hover:bg-[hsl(10,90%,55%)] transition-colors">
                τ
              </div>
              <span className="font-grotesk font-bold text-xl tracking-tight">torale</span>
            </a>
            
            <div className="hidden md:flex gap-8 text-sm font-medium text-zinc-500">
              <a href="#" className="hover:text-black transition-colors">Use Cases</a>
              <a href="#" className="hover:text-black transition-colors">Developers</a>
              <a href="#" className="hover:text-black transition-colors">Pricing</a>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button className="text-sm font-bold text-zinc-900 hover:underline px-3 py-2">Sign In</button>
            <button className="bg-zinc-900 text-white px-5 py-2 text-sm font-bold hover:bg-[hsl(10,90%,55%)] transition-colors shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] active:translate-y-[2px] active:shadow-none">
              Start Monitoring
            </button>
          </div>
        </div>
      </nav>

      <main className="relative z-10">
        
        {/* --- Hero Section --- */}
        <section className="relative pt-32 pb-24 px-6 border-b border-zinc-200 overflow-hidden">
          {/* Particle Network Animation */}
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
                <button className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-[hsl(10,90%,55%)] text-white text-lg font-bold hover:bg-[hsl(10,90%,50%)] transition-all shadow-[6px_6px_0px_0px_rgba(24,24,27,1)] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_rgba(24,24,27,1)] border-2 border-zinc-900">
                  Create Monitor
                  <ArrowRight className="h-5 w-5" />
                </button>
                
                <button className="group inline-flex items-center justify-center gap-2 px-8 py-4 bg-white hover:bg-zinc-50 transition-all font-bold text-zinc-900 border-2 border-zinc-200">
                  <Terminal className="h-4 w-4 text-zinc-400 group-hover:text-black" />
                  Documentation
                </button>
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

        {/* --- Architecture Section (Sticky Scroll - First Principles) --- */}
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

        {/* --- Use Cases / Logic Section --- */}
        <section className="py-24 px-6 bg-white border-t border-zinc-200">
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
                  &gt; Detected change on /pricing<br/>
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
                  &gt; New document found: "Amendment 45b"<br/>
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
                  &gt; CVE-2025-9921 Detected<br/>
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
                  &gt; Service: EC2 (us-east-1)<br/>
                  &gt; Status: <span className="text-amber-600 font-bold">DEGRADED</span>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* --- Developer Experience Section (The "Terminal" request) --- */}
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

        {/* --- Footer --- */}
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
                  <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">SDK</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Changelog</a></li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Developers</h4>
                <ul className="space-y-3 text-sm text-zinc-500 font-medium">
                  <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">API Reference</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Status</a></li>
                </ul>
              </div>

              <div>
                <h4 className="font-bold mb-6 text-white uppercase tracking-widest text-xs">Legal</h4>
                <ul className="space-y-3 text-sm text-zinc-500 font-medium">
                  <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
                </ul>
              </div>
            </div>

            <div className="border-t border-zinc-900 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="text-xs text-zinc-600 font-mono">
                [ © 2025 TORALE LABS INC. ]
              </div>
              <div className="flex gap-6">
                <GitBranch className="w-5 h-5 text-zinc-500 hover:text-white cursor-pointer transition-colors" />
                <Globe className="w-5 h-5 text-zinc-500 hover:text-white cursor-pointer transition-colors" />
              </div>
            </div>
          </div>
        </footer>

      </main>
    </div>
  );
}