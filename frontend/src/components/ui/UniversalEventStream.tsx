import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from '@/lib/motion-compat';
import {
  ShoppingBag,
  Gavel,
  AlertTriangle,
  Newspaper,
  TrendingUp,
  Globe,
} from 'lucide-react';

/**
 * UniversalEventStream - Animated event feed
 * From MockLandingPage.tsx lines 51-123
 */

interface Event {
  id: number;
  icon: typeof ShoppingBag;
  title: string;
  diff: string;
  source: string;
  color: string;
  bg: string;
}

export const UniversalEventStream = () => {
  const [events, setEvents] = useState<Event[]>([
    { id: 1, icon: ShoppingBag, title: "Tesla Model Y", diff: "$44,990 -> $42,990", source: "tesla.com", color: "text-blue-600", bg: "bg-blue-50" },
    { id: 2, icon: Gavel, title: "EU AI Act Update", diff: "New Article 45b added", source: "eur-lex.europa.eu", color: "text-purple-600", bg: "bg-purple-50" },
    { id: 3, icon: AlertTriangle, title: "CVE-2025-921", diff: "Severity: Critical (9.8)", source: "nvd.nist.gov", color: "text-red-600", bg: "bg-red-50" },
  ]);

  useEffect(() => {
    const stream: Omit<Event, 'id'>[] = [
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
