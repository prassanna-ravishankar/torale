import { useState, useEffect, useRef } from 'react';
import { motion, useScroll } from '@/lib/motion-compat';
import { Clock, Eye, Cpu, Zap } from 'lucide-react';

/**
 * TerminalLog & SystemTrace - Scroll-triggered system trace visualization
 * From MockLandingPage.tsx lines 168-313
 */

interface LogEntry {
  id: number;
  cmd: string;
  msg: string;
}

const TerminalLog = ({ activeStep }: { activeStep: number }) => {
  const steps: LogEntry[] = [
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

export const SystemTrace = () => {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  const [activeStep, setActiveStep] = useState(1);

  useEffect(() => {
    return scrollYProgress.on('change', (latest) => {
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
              <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 pointer-events-none bg-[length:100%_4px,3px_100%]" />

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
