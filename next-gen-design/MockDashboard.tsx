import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Search, 
  Plus, 
  Terminal, 
  Activity, 
  Clock, 
  Globe, 
  MoreHorizontal, 
  Zap, 
  CheckCircle2, 
  AlertCircle, 
  PauseCircle,
  PlayCircle,
  Filter,
  ArrowUpRight,
  Command,
  LayoutGrid,
  List as ListIcon
} from "lucide-react";

// --- Font Loader ---
const FontLoader = () => (
  <style dangerouslySetInnerHTML={{__html: `
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    .font-grotesk { font-family: 'Space Grotesk', sans-serif; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
  `}} />
);

// --- Types ---
type MonitorStatus = "active" | "paused" | "error" | "degraded";

interface Monitor {
  id: string;
  name: string;
  target: string;
  schedule: string;
  status: MonitorStatus;
  lastRun: string;
  successRate: number;
  tags: string[];
}

// --- Mock Data ---
const MOCK_MONITORS: Monitor[] = [
  {
    id: "mon_01",
    name: "Competitor Pricing Alpha",
    target: "competitor.com/enterprise",
    schedule: "*/5 * * * *",
    status: "active",
    lastRun: "2m ago",
    successRate: 99.8,
    tags: ["pricing", "competitors"]
  },
  {
    id: "mon_02",
    name: "EU Regulation Watch",
    target: "eur-lex.europa.eu/latest",
    schedule: "@hourly",
    status: "active",
    lastRun: "45m ago",
    successRate: 100,
    tags: ["legal", "eu"]
  },
  {
    id: "mon_03",
    name: "GPU Stock Scanner",
    target: "bestbuy.com/rtx-5090",
    schedule: "*/1 * * * *",
    status: "degraded",
    lastRun: "30s ago",
    successRate: 85.4,
    tags: ["inventory"]
  },
  {
    id: "mon_04",
    name: "SEC Filings - AAPL",
    target: "sec.gov/edgar/aapl",
    schedule: "@daily",
    status: "paused",
    lastRun: "1d ago",
    successRate: 100,
    tags: ["finance"]
  },
];

// --- Components ---

const StatusBadge = ({ status }: { status: MonitorStatus }) => {
  const styles = {
    active: "bg-emerald-50 text-emerald-600 border-emerald-200",
    paused: "bg-zinc-50 text-zinc-500 border-zinc-200",
    error: "bg-red-50 text-red-600 border-red-200",
    degraded: "bg-amber-50 text-amber-600 border-amber-200",
  };

  const icons = {
    active: <Activity className="w-3 h-3" />,
    paused: <PauseCircle className="w-3 h-3" />,
    error: <AlertCircle className="w-3 h-3" />,
    degraded: <Activity className="w-3 h-3" />,
  };

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-sm border text-[10px] font-mono uppercase tracking-wider ${styles[status]}`}>
      {icons[status]}
      {status}
    </div>
  );
};

const StatCard = ({ label, value, trend, trendUp }: { label: string, value: string, trend?: string, trendUp?: boolean }) => (
  <div className="bg-white p-4 border border-zinc-200 shadow-sm">
    <div className="text-[10px] font-mono uppercase text-zinc-400 mb-2">{label}</div>
    <div className="flex items-end justify-between">
      <div className="text-2xl font-bold font-grotesk text-zinc-900">{value}</div>
      {trend && (
        <div className={`text-xs font-mono flex items-center gap-1 ${trendUp ? 'text-emerald-600' : 'text-red-600'}`}>
          {trend}
          <ArrowUpRight className={`w-3 h-3 ${!trendUp && 'rotate-90'}`} />
        </div>
      )}
    </div>
  </div>
);

const MonitorCard = ({ monitor }: { monitor: Monitor }) => {
  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ y: -2, boxShadow: "0 10px 30px -10px rgba(0,0,0,0.1)" }}
      className="bg-white border border-zinc-200 group relative flex flex-col"
    >
      {/* Top Bar: Status & Actions */}
      <div className="p-4 border-b border-zinc-100 flex justify-between items-start">
        <div className="flex gap-2">
          <div className="p-2 bg-zinc-50 border border-zinc-100 rounded-sm text-zinc-500 group-hover:text-zinc-900 group-hover:border-zinc-300 transition-colors">
            <Globe className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-zinc-900 font-grotesk leading-tight mb-1">{monitor.name}</h3>
            <div className="flex items-center gap-2 text-[10px] text-zinc-400 font-mono">
              <span className="truncate max-w-[120px]">{monitor.target}</span>
            </div>
          </div>
        </div>
        <button className="text-zinc-400 hover:text-zinc-900 transition-colors">
          <MoreHorizontal className="w-4 h-4" />
        </button>
      </div>

      {/* Middle: Metrics */}
      <div className="p-4 grid grid-cols-2 gap-4 flex-1">
        <div>
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">Schedule</div>
          <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-600">
            <Clock className="w-3 h-3" />
            {monitor.schedule}
          </div>
        </div>
        <div>
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">Uptime</div>
          <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-600">
            <div className={`w-1.5 h-1.5 rounded-full ${monitor.successRate > 99 ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            {monitor.successRate}%
          </div>
        </div>
      </div>

      {/* Bottom: Footer */}
      <div className="bg-zinc-50 p-3 border-t border-zinc-100 flex justify-between items-center">
        <StatusBadge status={monitor.status} />
        <span className="text-[10px] text-zinc-400 font-mono">Run: {monitor.lastRun}</span>
      </div>

      {/* Hover Selection Border */}
      <div className="absolute inset-0 border-2 border-transparent group-hover:border-zinc-900 pointer-events-none transition-colors" />
    </motion.div>
  );
};

// --- Sidebar Navigation ---
const Sidebar = () => (
  <div className="w-64 bg-white border-r border-zinc-200 h-screen flex flex-col fixed left-0 top-0 z-40 hidden lg:flex">
    <div className="h-16 flex items-center px-6 border-b border-zinc-100">
      <div className="flex items-center gap-2">
        <div className="w-6 h-6 bg-zinc-900 text-white flex items-center justify-center font-grotesk font-bold rounded-sm">τ</div>
        <span className="font-grotesk font-bold text-lg tracking-tight">torale</span>
      </div>
    </div>

    <div className="p-4 space-y-8">
      <div>
        <div className="text-[10px] font-mono uppercase text-zinc-400 tracking-widest mb-3 px-2">Platform</div>
        <nav className="space-y-1">
          {[
            { icon: LayoutGrid, label: "Monitors", active: true },
            { icon: Activity, label: "Events" },
            { icon: Zap, label: "Webhooks" },
            { icon: Terminal, label: "Logs" },
          ].map((item) => (
            <button 
              key={item.label}
              className={`w-full flex items-center gap-3 px-2 py-2 text-sm font-medium rounded-sm transition-colors ${item.active ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50'}`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>
      </div>

      <div>
        <div className="text-[10px] font-mono uppercase text-zinc-400 tracking-widest mb-3 px-2">Configuration</div>
        <nav className="space-y-1">
          {[
            { icon: Globe, label: "Proxies" },
            { icon: CheckCircle2, label: "Verification" },
            { icon: Command, label: "API Keys" },
          ].map((item) => (
            <button 
              key={item.label}
              className="w-full flex items-center gap-3 px-2 py-2 text-sm font-medium text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50 rounded-sm transition-colors"
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>
      </div>
    </div>

    <div className="mt-auto p-4 border-t border-zinc-100">
      <div className="flex items-center gap-3 px-2">
        <div className="w-8 h-8 bg-gradient-to-br from-zinc-200 to-zinc-400 rounded-full" />
        <div className="text-xs">
          <div className="font-bold text-zinc-900">Engineering</div>
          <div className="text-zinc-400">Pro Plan</div>
        </div>
      </div>
    </div>
  </div>
);

// --- Main Dashboard Layout ---
export default function DashboardNextGen() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 font-sans selection:bg-[hsl(10,90%,55%)] selection:text-white">
      <FontLoader />
      
      <Sidebar />

      <main className="lg:ml-64 p-8">
        {/* Header Area */}
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono mb-2">
              <span>Organization</span>
              <span>/</span>
              <span className="text-zinc-900">Monitors</span>
            </div>
            <h1 className="text-3xl font-bold font-grotesk tracking-tight">Mission Control</h1>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <input 
                type="text" 
                placeholder="Search monitors..." 
                className="pl-9 pr-4 py-2 bg-white border border-zinc-200 rounded-sm text-sm focus:outline-none focus:border-zinc-400 w-64 shadow-sm"
              />
            </div>
            <button className="flex items-center gap-2 bg-zinc-900 text-white px-4 py-2 rounded-sm text-sm font-bold hover:bg-[hsl(10,90%,55%)] transition-colors shadow-md active:translate-y-[1px]">
              <Plus className="w-4 h-4" />
              New Monitor
            </button>
          </div>
        </header>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <StatCard label="Active Monitors" value="12" trend="+2" trendUp={true} />
          <StatCard label="Events (24h)" value="8,402" trend="+12%" trendUp={true} />
          <StatCard label="Success Rate" value="99.9%" trend="-0.1%" trendUp={false} />
          <StatCard label="Avg Latency" value="420ms" />
        </div>

        {/* Filters & View Toggle */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex gap-2">
            <button className="px-3 py-1.5 bg-white border border-zinc-200 rounded-sm text-xs font-medium text-zinc-600 hover:border-zinc-400 flex items-center gap-2">
              <Filter className="w-3 h-3" />
              Status: All
            </button>
            <button className="px-3 py-1.5 bg-white border border-zinc-200 rounded-sm text-xs font-medium text-zinc-600 hover:border-zinc-400 flex items-center gap-2">
              Tags: Any
            </button>
          </div>

          <div className="flex bg-white border border-zinc-200 rounded-sm p-0.5">
            <button 
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-sm transition-colors ${viewMode === 'grid' ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400 hover:text-zinc-600'}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button 
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-sm transition-colors ${viewMode === 'list' ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400 hover:text-zinc-600'}`}
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Monitors Grid */}
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
          <AnimatePresence>
            {MOCK_MONITORS.map((monitor) => (
              <MonitorCard key={monitor.id} monitor={monitor} />
            ))}
            
            {/* Add New Placeholder */}
            <motion.button
              layout
              className="border-2 border-dashed border-zinc-200 rounded-sm flex flex-col items-center justify-center p-8 text-zinc-400 hover:border-zinc-400 hover:text-zinc-600 transition-all group min-h-[200px]"
            >
              <div className="w-12 h-12 rounded-full bg-zinc-50 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                <Plus className="w-6 h-6" />
              </div>
              <span className="font-mono text-xs uppercase tracking-widest font-bold">Deploy New Monitor</span>
            </motion.button>
          </AnimatePresence>
        </div>

      </main>
    </div>
  );
}