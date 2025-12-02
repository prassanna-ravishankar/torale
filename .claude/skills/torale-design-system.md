# Torale Design System

Apply Torale's neo-brutalist design language to components and pages.

## Core Philosophy: "The Machine"

Torale is not a SaaS "service"; it is a **machine** that the user operates. The interface should feel like a high-precision instrument panel—dense, responsive, and brutally honest about system state.

## Typography: Tri-Font Stack

```typescript
// Font imports (already in project)
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
```

| Role | Font Family | Usage | Tailwind Classes |
|------|-------------|-------|------------------|
| **Structure** | Space Grotesk | Headings, KPIs, Nav Links | `font-grotesk font-bold` |
| **Data** | JetBrains Mono | IDs, Logs, Statuses, JSON | `font-mono` |
| **Narrative** | Inter | Body text, Tooltips, Help | `font-sans` |

## Color Palette: "Operational"

### Surface Colors
```typescript
Canvas: bg-zinc-50      // #FAFAFA
Cards: bg-white         // #FFFFFF
Terminal: bg-zinc-950   // #09090B
```

### Ink Colors
```typescript
Primary: text-zinc-900     // #18181B
Secondary: text-zinc-500   // #71717A
Tertiary: text-zinc-400    // #A1A1AA
```

### Signal Colors (Semantic Only)
```typescript
// Operational (Green)
text-emerald-600 bg-emerald-50 border-emerald-200

// Degraded (Amber)
text-amber-600 bg-amber-50 border-amber-200

// Critical (Red)
text-red-600 bg-red-50 border-red-200

// Action (Brand)
bg-[hsl(10,90%,55%)] // Primary buttons & active states
```

## Layout & Spacing

**Grid Unit:** 4px - All spacing must be multiples of 4

**Borders:**
- Standard: `border border-zinc-200`
- Active/Focus: `border-2 border-zinc-900`
- Hard Dividers: `border-2 border-zinc-100`

**Border Radius:**
- Small (tags, badges, inputs): `rounded-sm` (2px)
- Medium (cards, buttons): `rounded` (4px)
- Large (modals, containers): `rounded-lg` (8px)
- **No pill shapes** - prefer squared technical look

## Component Patterns

### Buttons

```typescript
// Primary Action
<button className="bg-zinc-900 text-white px-5 py-2 text-sm font-bold hover:bg-[hsl(10,90%,55%)] transition-colors shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] active:translate-y-[2px] active:shadow-none">
  Deploy Monitor
</button>

// Secondary
<button className="bg-white border-2 border-zinc-200 text-zinc-900 px-5 py-2 text-sm font-bold hover:border-zinc-400 transition-colors">
  Cancel
</button>

// Ghost
<button className="text-zinc-500 px-4 py-2 hover:bg-zinc-100 hover:text-zinc-900 transition-colors">
  View Details
</button>
```

### Inputs

```typescript
// Default
<input className="bg-white border border-zinc-200 px-3 py-2 rounded-sm focus:outline-none focus:border-zinc-900 focus:ring-0" />

// Error State
<input className="bg-red-50 border border-red-500 text-red-600 px-3 py-2 rounded-sm" />
```

### Status Badges

```typescript
// Active/Operational
<div className="inline-flex items-center gap-1.5 px-2 py-1 rounded-sm border bg-emerald-50 text-emerald-600 border-emerald-200 text-[10px] font-mono uppercase tracking-wider">
  <Activity className="w-3 h-3" />
  Active
</div>

// Degraded
<div className="inline-flex items-center gap-1.5 px-2 py-1 rounded-sm border bg-amber-50 text-amber-600 border-amber-200 text-[10px] font-mono uppercase tracking-wider">
  <AlertCircle className="w-3 h-3" />
  Degraded
</div>

// Critical/Error
<div className="inline-flex items-center gap-1.5 px-2 py-1 rounded-sm border bg-red-50 text-red-600 border-red-200 text-[10px] font-mono uppercase tracking-wider">
  <AlertTriangle className="w-3 h-3" />
  Critical
</div>
```

### Signal Cards (Dashboard)

The fundamental unit of the dashboard:

```typescript
<div className="bg-white border border-zinc-200 shadow-sm hover:shadow-md transition-shadow">
  {/* Header */}
  <div className="p-4 border-b border-zinc-100 flex justify-between items-start">
    <div>
      <h3 className="font-bold text-sm text-zinc-900 font-grotesk">{name}</h3>
      <div className="text-[10px] text-zinc-400 font-mono">{target}</div>
    </div>
  </div>

  {/* Metrics */}
  <div className="p-4 grid grid-cols-2 gap-4">
    <div>
      <div className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">Schedule</div>
      <div className="text-xs font-mono text-zinc-600">{schedule}</div>
    </div>
  </div>

  {/* Status Footer */}
  <div className="bg-zinc-50 p-3 border-t border-zinc-100 flex justify-between items-center">
    <StatusBadge status={status} />
    <span className="text-[10px] text-zinc-400 font-mono">Run: {lastRun}</span>
  </div>
</div>
```

## Animation Physics (Framer Motion)

### The "Snap" (Springs) - Layout Changes
```typescript
transition: { type: "spring", stiffness: 300, damping: 25 }
```

### The "Click" (Tap) - Buttons Feel Mechanical
```typescript
whileTap={{ scale: 0.98, y: 1 }}
```

### The "Lift" (Hover) - Cards Indicate Interactivity
```typescript
whileHover={{ y: -2, boxShadow: "0 10px 30px -10px rgba(0,0,0,0.1)" }}
```

## Microcopy & Voice

### Core Traits
- **Technical, not Jargon-heavy:** Use correct terms but explain why it matters
- **Active, not Passive:** "Monitor deployed" not "The monitor has been deployed"
- **Confident:** "Make the internet work for you" not "Try to monitor things"

### Examples

**Empty States:**
❌ "No items found"
✅ "System Idle. Deploy a monitor to begin."

**Buttons:**
✅ Deploy, Initialize, Terminate, Execute
❌ Submit, Click Here, Go

**Success Messages:**
✅ "Status: Nominal" / "200 OK" / "Synced"
❌ "Success!" / "Done!"

**Error Messages:**
✅ "Connection refused at port 443"
❌ "Something went wrong"

### The "Live" Narrative

Frame the system as **active**:
- "Scan interval: 5m. Next run in 2m." (not "Last updated: 5 mins ago")
- Use "Live Feed" or "Stream" metaphors over static lists
- Show system pulse with `animate-pulse` on status indicators

## Grid System

**Dashboard Layout:** Responsive grid over vertical lists

```typescript
// Mission Control Grid
<div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
  {monitors.map(monitor => <SignalCard key={monitor.id} {...monitor} />)}
</div>
```

**Why:** Users can scan a grid of 12 cards faster than a table of 12 rows to find the "Red" status.

## Design Rules

### Law of Common Region (Gestalt)
- **Never use whitespace alone** to separate content
- Use **2px borders** to define functional units
- **If it functions together, box it together**

### Doherty Threshold (Speed)
- Target <400ms for all interactions
- Use **optimistic UI** - update immediately before API responds
- Show system activity with `animate-pulse` on status dots

### No Over-Engineering
- Don't add decorative elements unless they serve a functional purpose
- Avoid rounded corners on large elements (use `rounded-sm` or `rounded`)
- Keep shadows sharp and minimal: `shadow-sm` or `shadow-md`

## When to Apply This Skill

Use this skill when:
- Creating new UI components
- Styling pages or layouts
- Choosing colors, fonts, or spacing
- Writing button labels or microcopy
- Designing status indicators or badges
- Building dashboard cards or grids

## Implementation Checklist

When creating a component:
- [ ] Uses correct font (Grotesk for headings, Mono for data, Sans for body)
- [ ] Spacing is multiples of 4px
- [ ] Borders are 1px (standard) or 2px (active/focus)
- [ ] Colors are semantic (operational/degraded/critical)
- [ ] Microcopy is active voice and technical
- [ ] Animations use spring physics for layout, tap for buttons, lift for cards
- [ ] Status indicators use `animate-pulse` to show activity
- [ ] Empty states use "system" language ("Idle", "Nominal", "Active")
