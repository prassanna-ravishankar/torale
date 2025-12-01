# Torale Component Library

Pre-built components following Torale's design system. Copy-paste these into your React components.

## Required Dependencies

```bash
npm install framer-motion lucide-react
```

## Font Setup (Add to root layout/app)

```typescript
// Add to app/layout.tsx or main.tsx
const FontLoader = () => (
  <style dangerouslySetInnerHTML={{__html: `
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    .font-grotesk { font-family: 'Space Grotesk', sans-serif; }
    .font-mono { font-family: 'JetBrains Mono', monospace; }
  `}} />
);
```

## Buttons

### Primary Action Button
```typescript
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

<motion.button
  whileTap={{ scale: 0.98, y: 1 }}
  className="inline-flex items-center gap-2 bg-zinc-900 text-white px-5 py-2 text-sm font-bold hover:bg-[hsl(10,90%,55%)] transition-colors shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] active:translate-y-[2px] active:shadow-none"
>
  Deploy Monitor
  <ArrowRight className="w-4 h-4" />
</motion.button>
```

### Secondary Button
```typescript
<motion.button
  whileTap={{ scale: 0.98 }}
  className="bg-white border-2 border-zinc-200 text-zinc-900 px-5 py-2 text-sm font-bold hover:border-zinc-400 transition-colors"
>
  Cancel
</motion.button>
```

### Ghost Button
```typescript
<button className="text-zinc-500 px-4 py-2 hover:bg-zinc-100 hover:text-zinc-900 transition-colors rounded-sm">
  View Details
</button>
```

## Status Badges

```typescript
import { Activity, AlertCircle, AlertTriangle, PauseCircle } from 'lucide-react';

type MonitorStatus = "active" | "paused" | "error" | "degraded";

const StatusBadge = ({ status }: { status: MonitorStatus }) => {
  const config = {
    active: {
      style: "bg-emerald-50 text-emerald-600 border-emerald-200",
      icon: Activity,
      label: "Active"
    },
    paused: {
      style: "bg-zinc-50 text-zinc-500 border-zinc-200",
      icon: PauseCircle,
      label: "Paused"
    },
    error: {
      style: "bg-red-50 text-red-600 border-red-200",
      icon: AlertTriangle,
      label: "Error"
    },
    degraded: {
      style: "bg-amber-50 text-amber-600 border-amber-200",
      icon: AlertCircle,
      label: "Degraded"
    }
  };

  const { style, icon: Icon, label } = config[status];

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-sm border text-[10px] font-mono uppercase tracking-wider ${style}`}>
      <Icon className="w-3 h-3" />
      {label}
    </div>
  );
};
```

## Signal Card (Dashboard Monitor Card)

```typescript
import { motion } from 'framer-motion';
import { Globe, Clock, MoreHorizontal } from 'lucide-react';

interface Monitor {
  id: string;
  name: string;
  target: string;
  schedule: string;
  status: "active" | "paused" | "error" | "degraded";
  lastRun: string;
  successRate: number;
}

const SignalCard = ({ monitor }: { monitor: Monitor }) => {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, boxShadow: "0 10px 30px -10px rgba(0,0,0,0.1)" }}
      className="bg-white border border-zinc-200 group relative flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-zinc-100 flex justify-between items-start">
        <div className="flex gap-2">
          <div className="p-2 bg-zinc-50 border border-zinc-100 rounded-sm text-zinc-500 group-hover:text-zinc-900 group-hover:border-zinc-300 transition-colors">
            <Globe className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-zinc-900 font-grotesk leading-tight mb-1">
              {monitor.name}
            </h3>
            <div className="text-[10px] text-zinc-400 font-mono truncate max-w-[120px]">
              {monitor.target}
            </div>
          </div>
        </div>
        <button className="text-zinc-400 hover:text-zinc-900 transition-colors">
          <MoreHorizontal className="w-4 h-4" />
        </button>
      </div>

      {/* Metrics */}
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

      {/* Footer */}
      <div className="bg-zinc-50 p-3 border-t border-zinc-100 flex justify-between items-center">
        <StatusBadge status={monitor.status} />
        <span className="text-[10px] text-zinc-400 font-mono">Run: {monitor.lastRun}</span>
      </div>

      {/* Hover Border */}
      <div className="absolute inset-0 border-2 border-transparent group-hover:border-zinc-900 pointer-events-none transition-colors" />
    </motion.div>
  );
};
```

## Stat Card (KPI Display)

```typescript
import { ArrowUpRight } from 'lucide-react';

const StatCard = ({
  label,
  value,
  trend,
  trendUp
}: {
  label: string;
  value: string;
  trend?: string;
  trendUp?: boolean;
}) => (
  <div className="bg-white p-4 border border-zinc-200 shadow-sm">
    <div className="text-[10px] font-mono uppercase text-zinc-400 mb-2 tracking-wider">
      {label}
    </div>
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

// Usage
<StatCard label="Active Monitors" value="12" trend="+2" trendUp={true} />
<StatCard label="Success Rate" value="99.9%" trend="-0.1%" trendUp={false} />
```

## Input Field

```typescript
const Input = ({
  label,
  error,
  ...props
}: {
  label?: string;
  error?: string;
} & React.InputHTMLAttributes<HTMLInputElement>) => (
  <div className="space-y-1">
    {label && (
      <label className="text-xs font-mono uppercase tracking-wider text-zinc-600">
        {label}
      </label>
    )}
    <input
      className={`w-full px-3 py-2 rounded-sm text-sm transition-colors
        ${error
          ? 'bg-red-50 border border-red-500 text-red-600 focus:outline-none focus:border-red-600'
          : 'bg-white border border-zinc-200 focus:outline-none focus:border-zinc-900'
        }`}
      {...props}
    />
    {error && (
      <p className="text-xs text-red-600 font-mono">{error}</p>
    )}
  </div>
);

// Usage
<Input label="Monitor Name" placeholder="Competitor Pricing" />
<Input label="Target URL" error="Invalid URL format" />
```

## Terminal Block

```typescript
const TerminalBlock = ({ children }: { children: React.ReactNode }) => (
  <div className="bg-zinc-950 rounded-lg overflow-hidden border border-zinc-800 font-mono text-sm">
    {/* Header */}
    <div className="bg-zinc-900 px-4 py-2 flex items-center gap-2 border-b border-zinc-800">
      <div className="flex gap-1.5">
        <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
        <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
        <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
      </div>
      <div className="ml-auto text-zinc-600 text-xs">user@dev:~</div>
    </div>

    {/* Content */}
    <div className="p-6 text-zinc-300">
      {children}
    </div>
  </div>
);

// Usage
<TerminalBlock>
  <div className="flex gap-2">
    <span className="text-[hsl(10,90%,55%)]">➜</span>
    <span>npm install torale</span>
  </div>
</TerminalBlock>
```

## Live Status Indicator

```typescript
const LiveIndicator = ({ label }: { label: string }) => (
  <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border-2 border-zinc-900 text-zinc-900 text-xs font-mono font-bold uppercase tracking-wider shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]">
    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
    {label}
  </div>
);

// Usage
<LiveIndicator label="System: Nominal" />
<LiveIndicator label="Live Feed" />
```

## Section Header

```typescript
import { motion } from 'framer-motion';

const SectionHeader = ({
  title,
  subtitle,
  label
}: {
  title: string;
  subtitle: string;
  label?: string;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    className="flex flex-col md:flex-row justify-between items-start md:items-end mb-16 border-b-2 border-zinc-100 pb-8"
  >
    <div className="max-w-2xl">
      <h2 className="text-4xl md:text-5xl font-bold font-grotesk tracking-tight mb-4 text-zinc-900">
        {title}
      </h2>
      <p className="text-zinc-500 text-lg font-light leading-relaxed max-w-xl">
        {subtitle}
      </p>
    </div>
    {label && (
      <span className="font-mono text-sm font-bold text-zinc-300 mt-4 md:mt-0 tracking-widest uppercase">
        [{label}]
      </span>
    )}
  </motion.div>
);

// Usage
<SectionHeader
  title="System Architecture"
  subtitle="We re-engineered the monitoring stack to eliminate flakiness."
  label="ARCHITECTURE"
/>
```

## Empty State

```typescript
import { Plus } from 'lucide-react';

const EmptyState = ({
  icon: Icon = Plus,
  title,
  action
}: {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  action?: () => void;
}) => (
  <motion.button
    onClick={action}
    className="border-2 border-dashed border-zinc-200 rounded-sm flex flex-col items-center justify-center p-12 text-zinc-400 hover:border-zinc-400 hover:text-zinc-600 transition-all group min-h-[200px]"
  >
    <div className="w-12 h-12 rounded-full bg-zinc-50 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
      <Icon className="w-6 h-6" />
    </div>
    <span className="font-mono text-xs uppercase tracking-widest font-bold">
      {title}
    </span>
  </motion.button>
);

// Usage
<EmptyState
  title="System Idle. Deploy a monitor to begin."
  action={() => console.log('Create monitor')}
/>
```

## When to Use

- Copy these components directly into your React files
- Customize props and content while maintaining the visual style
- Use as templates for building similar components
- Refer to design system skill for color/spacing/typography rules
