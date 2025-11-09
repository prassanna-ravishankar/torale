import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { Zap, TrendingUp, Bug, ArrowLeft, Server, FlaskConical } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/card";
import { AnimatedBackground } from "./AnimatedBackground";

interface ChangelogEntry {
  id: string;
  date: string;
  title: string;
  description: string;
  category: "feature" | "improvement" | "fix" | "infra" | "research";
  requestedBy: string[];
  pr?: number; // Optional PR number
}

const getCategoryIcon = (category: string) => {
  switch (category) {
    case "feature":
      return Zap;
    case "improvement":
      return TrendingUp;
    case "fix":
      return Bug;
    case "infra":
      return Server;
    case "research":
      return FlaskConical;
    default:
      return Zap;
  }
};

const getCategoryLabel = (category: string) => {
  switch (category) {
    case "feature":
      return "New Feature";
    case "improvement":
      return "Improvement";
    case "fix":
      return "Bug Fix";
    case "infra":
      return "Infrastructure";
    case "research":
      return "Research";
    default:
      return "Update";
  }
};

export default function Changelog() {
  const navigate = useNavigate();
  const [entries, setEntries] = useState<ChangelogEntry[]>([]);
  const [mounted, setMounted] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  // Parallax effect for timeline
  const timelineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  useEffect(() => {
    setMounted(true);

    const fetchChangelog = async () => {
      try {
        const response = await fetch("/changelog.json");
        if (response.ok) {
          const data = await response.json();
          setEntries(data);
        }
      } catch (error) {
        console.error("Failed to fetch changelog:", error);
      }
    };

    fetchChangelog();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/20 relative">
      {/* Animated Background with reduced opacity */}
      <div className="fixed inset-0 pointer-events-none z-0 opacity-60">
        <AnimatedBackground />
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/20 bg-background/10 backdrop-blur-md">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/brand/svg/logo-cropped.svg" alt="Torale" className="h-10 w-10" />
            <span className="text-2xl font-bold">τorale</span>
          </div>
          <button
            onClick={() => navigate("/")}
            className="inline-flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="pt-32 pb-20 px-6" ref={containerRef}>
        <div className="container mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={mounted ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8 }}
            className="sticky top-20 z-40 bg-gradient-to-b from-background via-background to-background/80 backdrop-blur-sm pb-8 mb-12 text-center"
          >
            <h1 className="text-4xl md:text-5xl font-bold mb-4">What's New</h1>
            <p className="text-lg text-muted-foreground mb-3 max-w-2xl mx-auto">
              Torale is built in the open. Every feature, improvement, and bug fix is shaped by real user feedback
              and shared publicly. Follow along as we build a better way to monitor the web.
            </p>
            <p className="text-sm text-muted-foreground/70">
              <a
                href="https://github.com/prassanna-ravishankar/torale"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline inline-flex items-center gap-1"
              >
                View source on GitHub →
              </a>
            </p>
          </motion.div>

          {/* Timeline */}
          <div className="relative">
            {/* Timeline line - gray background */}
            <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-border -translate-x-1/2" />

            {/* Timeline progress - primary color fills as you scroll */}
            <motion.div
              className="absolute left-1/2 top-0 w-0.5 bg-primary -translate-x-1/2"
              style={{ height: timelineHeight }}
            />

            {/* Entries */}
            <div className="space-y-12">
              {entries.map((entry, index) => {
                const IconComponent = getCategoryIcon(entry.category);
                const isEven = index % 2 === 0;

                return (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, x: isEven ? -50 : 50 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: false, margin: "-200px" }}
                    transition={{ duration: 0.6, delay: 0.1 }}
                    className="relative"
                  >
                    {/* Timeline dot */}
                    <motion.div
                      className="absolute left-1/2 top-6 w-3 h-3 rounded-full border-4 border-background -translate-x-1/2 z-10"
                      initial={{ scale: 1, backgroundColor: "hsl(var(--muted-foreground) / 0.3)" }}
                      whileInView={{ scale: 1.3, backgroundColor: "hsl(var(--primary))" }}
                      viewport={{ margin: "-200px" }}
                      transition={{ duration: 0.3 }}
                    />

                    {/* Content */}
                    <div className={`grid grid-cols-2 gap-8 ${isEven ? "" : ""}`}>
                      {isEven ? (
                        <>
                          {/* Content on left */}
                          <div className="text-right">
                            <motion.div
                              className="rounded-lg border-2 overflow-hidden"
                              initial={{ borderColor: "hsl(var(--border))" }}
                              whileInView={{ borderColor: "hsl(var(--primary))", scale: 1.02 }}
                              viewport={{ margin: "-200px" }}
                              transition={{ duration: 0.3 }}
                            >
                              <Card className="border-0">
                                <motion.div
                                  className="absolute inset-0 bg-gradient-to-br from-primary/3 to-transparent"
                                  initial={{ opacity: 0 }}
                                  whileInView={{ opacity: 1 }}
                                  viewport={{ margin: "-200px" }}
                                  transition={{ duration: 0.3 }}
                                />
                              <CardHeader className="p-6 relative">
                                <div className="flex flex-col items-end">
                                  <div className="flex items-center gap-2 mb-1">
                                    {entry.pr && (
                                      <a
                                        href={`https://github.com/prassanna-ravishankar/torale/pull/${entry.pr}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[10px] font-mono text-muted-foreground/70 hover:text-primary hover:underline transition-colors"
                                        title="View PR on GitHub"
                                      >
                                        #{entry.pr}
                                      </a>
                                    )}
                                    <span className="text-xs text-muted-foreground">
                                      {new Date(entry.date).toLocaleDateString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric",
                                      })}
                                    </span>
                                    <span className="text-[9px] font-semibold uppercase tracking-wide text-primary">
                                      {getCategoryLabel(entry.category)}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-3 mb-2">
                                    <h3 className="text-lg font-bold group-hover:text-primary transition-colors">
                                      {entry.title}
                                    </h3>
                                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/15 transition-colors">
                                      <IconComponent className="h-5 w-5 text-primary" />
                                    </div>
                                  </div>
                                  <p className="text-sm text-muted-foreground leading-relaxed text-right">
                                    {entry.description}
                                  </p>
                                  {entry.requestedBy.length > 0 && (
                                    <p className="text-xs text-muted-foreground/70 mt-3">
                                      Requested by {entry.requestedBy.join(", ")}
                                    </p>
                                  )}
                                </div>
                              </CardHeader>
                            </Card>
                            </motion.div>
                          </div>
                          {/* Empty space on right */}
                          <div />
                        </>
                      ) : (
                        <>
                          {/* Empty space on left */}
                          <div />
                          {/* Content on right */}
                          <div>
                            <motion.div
                              className="rounded-lg border-2 overflow-hidden"
                              initial={{ borderColor: "hsl(var(--border))" }}
                              whileInView={{ borderColor: "hsl(var(--primary))", scale: 1.02 }}
                              viewport={{ margin: "-200px" }}
                              transition={{ duration: 0.3 }}
                            >
                              <Card className="border-0">
                                <motion.div
                                  className="absolute inset-0 bg-gradient-to-br from-primary/3 to-transparent"
                                  initial={{ opacity: 0 }}
                                  whileInView={{ opacity: 1 }}
                                  viewport={{ margin: "-200px" }}
                                  transition={{ duration: 0.3 }}
                                />
                              <CardHeader className="p-6 relative">
                                <div className="flex flex-col items-start">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="text-[9px] font-semibold uppercase tracking-wide text-primary">
                                      {getCategoryLabel(entry.category)}
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                      {new Date(entry.date).toLocaleDateString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        year: "numeric",
                                      })}
                                    </span>
                                    {entry.pr && (
                                      <a
                                        href={`https://github.com/prassanna-ravishankar/torale/pull/${entry.pr}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[10px] font-mono text-muted-foreground/70 hover:text-primary hover:underline transition-colors"
                                        title="View PR on GitHub"
                                      >
                                        #{entry.pr}
                                      </a>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-3 mb-2">
                                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/15 transition-colors">
                                      <IconComponent className="h-5 w-5 text-primary" />
                                    </div>
                                    <h3 className="text-lg font-bold group-hover:text-primary transition-colors">
                                      {entry.title}
                                    </h3>
                                  </div>
                                  <p className="text-sm text-muted-foreground leading-relaxed">
                                    {entry.description}
                                  </p>
                                  {entry.requestedBy.length > 0 && (
                                    <p className="text-xs text-muted-foreground/70 mt-3">
                                      Requested by {entry.requestedBy.join(", ")}
                                    </p>
                                  )}
                                </div>
                              </CardHeader>
                            </Card>
                            </motion.div>
                          </div>
                        </>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
