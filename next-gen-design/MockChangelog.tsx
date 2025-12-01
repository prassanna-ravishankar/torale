import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  GitCommit, 
  ArrowLeft, 
  Github, 
  Tag, 
  Calendar, 
  ArrowUpRight,
  Zap,
  CheckCircle2,
  Bug,
  LayoutTemplate
} from "lucide-react";

// --- Font Loader (Same as Design System) ---
const FontLoader = () => (
  <style dangerouslySetInnerHTML={{__html: `
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    .font-grotesk { font-family: 'Space Grotesk', sans-serif; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
  `}} />
);

// --- Types ---
type ChangeType = "feature" | "improvement" | "fix";

interface ChangelogEntry {
  id: string;
  version?: string;
  date: string;
  type: ChangeType;
  title: string;
  description: string;
  image?: string; 
}

// --- Mock Data ---
const CHANGES: ChangelogEntry[] = [
  {
    id: "91",
    date: "Dec 1, 2025",
    type: "improvement",
    title: "Critical UX Improvements & Bug Fixes",
    description: "Major quality-of-life update fixing several critical issues: email notifications now send reliably with proper Novu integration, task status badges show accurate states with last execution tracking, timezone displays work correctly across the app.",
  },
  {
    id: "81",
    date: "Nov 29, 2025",
    type: "improvement",
    title: "Simplified Task Creation Experience",
    description: "Completely redesigned task creation with a streamlined single-page dialog. Removed the multi-step wizard in favor of progressive disclosure for advanced options. Added instant task execution after creation.",
  },
  {
    id: "78",
    date: "Nov 18, 2025",
    type: "feature",
    title: "Comprehensive Documentation Site",
    description: "Launched docs.torale.ai with complete platform documentation. Includes user guides, API reference, SDK documentation, CLI commands, architecture diagrams, and deployment guides.",
  },
  {
    id: "76",
    date: "Nov 17, 2025",
    type: "feature",
    title: "Developer API Portal & SDK Examples",
    description: "Build with Torale programmatically. New developer portal lets admins generate API keys and manage team roles. Complete Python SDK documentation with runnable examples.",
  }
];

// --- Components ---

const TypeBadge = ({ type }: { type: ChangeType }) => {
  const styles = {
    feature: "bg-emerald-50 text-emerald-700 border-emerald-200",
    improvement: "bg-blue-50 text-blue-700 border-blue-200",
    fix: "bg-amber-50 text-amber-700 border-amber-200",
  };

  const labels = {
    feature: "NEW FEATURE",
    improvement: "IMPROVEMENT",
    fix: "BUG FIX",
  };

  const icons = {
    feature: <Zap className="w-3 h-3" />,
    improvement: <CheckCircle2 className="w-3 h-3" />,
    fix: <Bug className="w-3 h-3" />,
  };

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-sm border text-[10px] font-mono font-bold tracking-wider uppercase ${styles[type]}`}>
      {icons[type]}
      {labels[type]}
    </div>
  );
};

const TimelineItem = ({ entry, index }: { entry: ChangelogEntry; index: number }) => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-10%" }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="relative pl-8 md:pl-0 group"
    >
      {/* Timeline Connector (Mobile: Left, Desktop: Center) */}
      <div className="absolute left-0 md:left-1/2 top-0 bottom-0 w-px bg-zinc-200 -ml-px md:-ml-0.5" />
      
      {/* Timeline Node */}
      <div className="absolute left-0 md:left-1/2 top-8 w-3 h-3 bg-white border-2 border-zinc-300 rounded-full -ml-1.5 md:-ml-1.5 z-10 group-hover:border-zinc-900 group-hover:scale-125 transition-all duration-300" />

      {/* Content Card Layout */}
      <div className={`md:flex items-start justify-between md:gap-12 ${index % 2 === 0 ? 'md:flex-row-reverse' : ''}`}>
        
        {/* Date / Meta (Opposite side on Desktop) */}
        <div className={`hidden md:block w-1/2 pt-8 ${index % 2 === 0 ? 'text-left pl-12' : 'text-right pr-12'}`}>
          <div className="font-mono text-sm text-zinc-400 mb-1">{entry.date}</div>
          <div className="font-mono text-xs text-zinc-300">#{entry.id}</div>
        </div>

        {/* Card (Main Side) */}
        <div className={`w-full md:w-1/2 mb-12 md:mb-24 ${index % 2 === 0 ? 'md:pr-12' : 'md:pl-12'}`}>
          {/* Mobile Date Header */}
          <div className="md:hidden mb-2 pl-4">
             <span className="font-mono text-xs text-zinc-400">{entry.date}</span>
          </div>

          <motion.div 
            whileHover={{ y: -2, boxShadow: "0 10px 30px -10px rgba(0,0,0,0.05)" }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="bg-white border border-zinc-200 p-6 md:p-8 rounded-lg shadow-sm transition-colors hover:border-zinc-300 relative group/card"
          >
            {/* Decorative Corner */}
            <div className="absolute top-0 right-0 w-8 h-8 overflow-hidden">
               <div className="absolute top-0 right-0 w-[150%] h-[150%] bg-zinc-50 rotate-45 transform origin-bottom-left border-l border-zinc-100"></div>
            </div>

            <div className="flex justify-between items-start mb-4">
              <TypeBadge type={entry.type} />
            </div>

            <h3 className="text-2xl font-bold font-grotesk text-zinc-900 mb-4 leading-tight">
              {entry.title}
            </h3>

            <p className="text-zinc-600 leading-relaxed text-sm md:text-base font-normal">
              {entry.description}
            </p>

            {/* Footer Metadata in Card */}
            <div className="mt-6 pt-4 border-t border-zinc-100 flex items-center justify-between">
               <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
                 <GitCommit className="w-3 h-3" />
                 <span>Commit: {entry.id}</span>
               </div>
               {/* "Requested by" could be dynamic */}
               {entry.type === 'improvement' && (
                 <div className="text-[10px] text-zinc-400 italic">
                   Community Request
                 </div>
               )}
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
};

export default function ChangelogNextGen() {
  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 font-sans selection:bg-[hsl(10,90%,55%)] selection:text-white">
      <FontLoader />
      
      {/* Background Grid */}
      <div 
        className="fixed inset-0 pointer-events-none z-0 opacity-[0.3]"
        style={{
          backgroundImage: `radial-gradient(#a1a1aa 1px, transparent 1px)`,
          backgroundSize: '32px 32px'
        }}
      />

      {/* Navigation Bar */}
      <nav className="sticky top-0 z-50 bg-[#fafafa]/90 backdrop-blur-md border-b border-zinc-200">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <a href="/" className="group flex items-center gap-2 text-zinc-500 hover:text-zinc-900 transition-colors">
              <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
              <span className="text-sm font-medium">Back to Home</span>
            </a>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-zinc-900 text-white flex items-center justify-center font-grotesk font-bold rounded-sm text-xs">τ</div>
            <span className="font-grotesk font-bold text-lg tracking-tight">torale</span>
          </div>

          <div className="w-[100px]"></div> {/* Spacer for centering logo */}
        </div>
      </nav>

      <main className="relative z-10 pb-32">
        {/* Header Section */}
        <section className="pt-24 pb-16 px-6 text-center">
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 bg-zinc-100 border border-zinc-200 rounded-full text-[10px] font-mono font-medium tracking-widest uppercase mb-6"
          >
            <div className="w-2 h-2 bg-[hsl(10,90%,55%)] rounded-full animate-pulse" />
            Live Feed
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold font-grotesk tracking-tight mb-6 text-zinc-900"
          >
            What's New
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg md:text-xl text-zinc-500 max-w-2xl mx-auto leading-relaxed mb-10"
          >
            Torale is built in the open. Every feature, improvement, and bug fix is shaped by real user feedback.
          </motion.p>

          <motion.a 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            href="https://github.com/prasadcode/torale"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-bold text-zinc-900 hover:text-[hsl(10,90%,55%)] transition-colors border-b border-zinc-900 hover:border-[hsl(10,90%,55%)] pb-0.5"
          >
            <Github className="w-4 h-4" />
            View Source on GitHub
            <ArrowUpRight className="w-3 h-3" />
          </motion.a>
        </section>

        {/* Timeline Section */}
        <div className="container mx-auto max-w-5xl px-6 relative">
          {/* Top Gradient Fade for Line */}
          <div className="absolute top-0 left-0 md:left-1/2 w-px h-16 bg-gradient-to-b from-transparent to-zinc-200 -ml-px md:-ml-0.5" />
          
          <div className="pt-16">
            {CHANGES.map((entry, index) => (
              <TimelineItem key={entry.id} entry={entry} index={index} />
            ))}
          </div>
          
          {/* Bottom "End of Line" Marker */}
          <motion.div 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="flex justify-center mt-12 relative z-10"
          >
            <div className="px-4 py-2 bg-zinc-100 border border-zinc-200 rounded-full text-xs font-mono text-zinc-400">
              Initial Release • Oct 2025
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}