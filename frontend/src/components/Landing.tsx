import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { motion, useScroll, useTransform } from "framer-motion";
import { Bell, Search, Sparkles, ArrowRight } from "lucide-react";

export default function Landing() {
  const navigate = useNavigate();
  const { isSignedIn } = useAuth();
  const { scrollYProgress } = useScroll();
  const [mounted, setMounted] = useState(false);

  // Parallax effects
  const heroY = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.3], [1, 0]);

  useEffect(() => {
    setMounted(true);
    if (isSignedIn) {
      navigate("/");
    }
  }, [isSignedIn, navigate]);

  const handleGetStarted = () => {
    navigate("/sign-up");
  };

  const examples = [
    "When is the next iPhone release date announced?",
    "When do swimming pool memberships open for summer?",
    "When is PS5 back in stock at Best Buy?",
    "When is the GPT-5 launch date confirmed?"
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/20">
      {/* Header */}
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className="fixed top-0 left-0 right-0 z-50 border-b bg-background/80 backdrop-blur-lg"
      >
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="h-6 w-6 text-primary" />
            <span className="text-xl font-semibold">Torale</span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate("/sign-in")}
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
        <div className="container mx-auto max-w-4xl text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={mounted ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.8 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 rounded-full bg-primary/10 text-primary text-sm font-medium">
              <Sparkles className="h-4 w-4" />
              Free during beta
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

          {/* Floating elements */}
          <motion.div
            animate={{
              y: [0, -20, 0],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className="absolute top-40 left-10 opacity-20"
          >
            <Search className="h-24 w-24 text-primary" />
          </motion.div>
          <motion.div
            animate={{
              y: [0, 20, 0],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            className="absolute top-60 right-10 opacity-20"
          >
            <Bell className="h-20 w-20 text-primary" />
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
            {[
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
            ].map((item, index) => (
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
            {examples.map((example, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="p-6 rounded-xl bg-card border hover:border-primary/50 transition-colors cursor-pointer group"
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
              Free during beta.
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
              <a href="https://torale.ai" className="hover:text-foreground transition-colors">
                torale.ai
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
