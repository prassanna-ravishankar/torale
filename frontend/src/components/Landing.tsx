import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { Bell, Search, Sparkles, ArrowRight, Code, Terminal } from "lucide-react";
import { AnimatedBackground } from "./AnimatedBackground";

const EXAMPLES = [
  "When is the iPhone 18 release date announced?",
  "When do swimming pool memberships open at Lido London?",
  "When is PS5 back in stock at Best Buy?",
  "When is the next OpenAI model launch date confirmed?"
];

const HOW_IT_WORKS = [
  {
    step: "1",
    title: "Ask a question",
    description:
      "What do you want to know? We search the web for answers.",
    icon: Search,
  },
  {
    step: "2",
    title: "Set a condition",
    description:
      "When should we notify you? Define what change matters.",
    icon: Sparkles,
  },
  {
    step: "3",
    title: "Get notified",
    description:
      "We monitor continuously and alert you the moment it happens.",
    icon: Bell,
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const { scrollYProgress } = useScroll();
  const [mounted, setMounted] = useState(false);

  // Parallax effects
  const heroY = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.3], [1, 0]);
  const backgroundY = useTransform(scrollYProgress, [0, 1], ["0%", "30%"]); // Slower than content
  const backgroundOpacity = useTransform(scrollYProgress, [0, 0.15, 0.35], [0.5, 0.5, 0]); // Fade out at use cases section

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleGetStarted = () => {
    navigate("/sign-up");
  };

  const handleSignIn = () => {
    navigate("/sign-in");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/20 relative">
      {/* Full Page Animated Background with Parallax and Fade */}
      <motion.div
        style={{ y: backgroundY, opacity: backgroundOpacity }}
        className="fixed inset-0 pointer-events-none z-0"
      >
        <AnimatedBackground />
      </motion.div>

      {/* Header */}
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="fixed top-0 left-0 right-0 z-50 border-b border-border/20 bg-white/10 backdrop-blur-md"
      >
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="h-6 w-6 text-primary" />
            <span className="text-xl font-semibold">Torale</span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleSignIn}
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Sign in
            </button>
            <button
              onClick={handleGetStarted}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              Get started
            </button>
          </div>
        </div>
      </motion.header>

      {/* Hero Section */}
      <motion.section
        style={{ y: heroY, opacity }}
        className="relative pt-32 pb-20 px-6 overflow-hidden"
      >

        <div className="container mx-auto max-w-4xl text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={mounted ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 rounded-full bg-primary/10 text-primary text-sm font-medium">
              <Sparkles className="h-4 w-4" />
              Free till I figure out what this is used for
            </div>
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
              Monitor the web.
              <br />
              Get notified when it matters.
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground mb-12 max-w-2xl mx-auto">
              Set it and forget it. Torale watches the web for you and notifies you
              when your conditions are met.
            </p>
            <button
              onClick={handleGetStarted}
              className="group inline-flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground rounded-lg text-lg font-medium hover:bg-primary/90 transition-all hover:gap-3"
            >
              Start monitoring
              <ArrowRight className="h-5 w-5 transition-all" />
            </button>
          </motion.div>
        </div>
      </motion.section>

      {/* How It Works */}
      <section className="py-20 px-6">
        <div className="container mx-auto max-w-5xl">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Simple. Powerful. Automatic.
            </h2>
            <p className="text-lg text-muted-foreground">
              Three steps to never miss what matters
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-12">
            {HOW_IT_WORKS.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                className="relative"
              >
                <div className="flex flex-col items-center text-center">
                  <div className="mb-4 h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center">
                    <item.icon className="h-8 w-8 text-primary" />
                  </div>
                  <div className="absolute -top-2 -left-2 h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                    {item.step}
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                  <p className="text-muted-foreground">{item.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Examples */}
      <section className="py-20 px-6 bg-muted/30">
        <div className="container mx-auto max-w-4xl">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Use cases
            </h2>
            <p className="text-lg text-muted-foreground">
              Monitor anything that changes on the web
            </p>
          </motion.div>

          <div className="space-y-4">
            {EXAMPLES.map((example, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="p-6 rounded-xl bg-card border hover:border-primary/50 transition-colors group"
              >
                <div className="flex items-center gap-4">
                  <div className="h-2 w-2 rounded-full bg-primary flex-shrink-0"></div>
                  <p className="text-lg group-hover:text-primary transition-colors">
                    {example}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Built for Developers */}
      <section className="py-20 px-6">
        <div className="container mx-auto max-w-5xl">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 mb-4 rounded-full bg-primary/10 text-primary text-sm font-medium">
              <Sparkles className="h-4 w-4" />
              Docs coming soon
            </div>
            <h2 className="text-3xl md:text-5xl font-bold mb-4">
              Built for developers too
            </h2>
            <p className="text-lg text-muted-foreground">
              REST API and CLI for programmatic monitoring
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6 }}
              className="p-8 rounded-2xl bg-card border"
            >
              <div className="mb-4 h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Code className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-2xl font-semibold mb-3">REST API</h3>
              <p className="text-muted-foreground mb-4">
                Full-featured API for creating and managing monitoring tasks programmatically
              </p>
              <div className="bg-muted/50 rounded-lg p-4 font-mono text-sm overflow-x-auto">
                <div className="text-muted-foreground">POST /api/v1/tasks</div>
                <div className="text-muted-foreground">GET /api/v1/tasks</div>
                <div className="text-muted-foreground">GET /api/v1/tasks/:id/executions</div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="p-8 rounded-2xl bg-card border"
            >
              <div className="mb-4 h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Terminal className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-2xl font-semibold mb-3">CLI</h3>
              <p className="text-muted-foreground mb-4">
                Manage monitors from your terminal with our command-line interface
              </p>
              <div className="bg-muted/50 rounded-lg p-4 font-mono text-sm overflow-x-auto">
                <div className="text-muted-foreground">$ torale task create \</div>
                <div className="text-muted-foreground ml-4">--query "..." \</div>
                <div className="text-muted-foreground ml-4">--condition "..."</div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-32 px-6">
        <div className="container mx-auto max-w-3xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-4xl md:text-6xl font-bold mb-6">
              Ready to get started?
            </h2>
            <p className="text-xl text-muted-foreground mb-8">
              Join early users monitoring the web automatically.
              <br />
              (It's free while I figure this out)
            </p>
            <button
              onClick={handleGetStarted}
              className="group inline-flex items-center gap-2 px-8 py-4 bg-primary text-primary-foreground rounded-lg text-lg font-medium hover:bg-primary/90 transition-all hover:gap-3"
            >
              Create your first monitor
              <ArrowRight className="h-5 w-5 transition-all" />
            </button>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Bell className="h-5 w-5" />
              <span>© 2025 Torale. Monitor what matters.</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <a href="https://torale.ai" target="_blank" rel="noopener noreferrer" className="hover:text-foreground transition-colors">
                torale.ai
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
