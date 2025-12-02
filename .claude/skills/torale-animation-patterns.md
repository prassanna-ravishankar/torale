# Torale Animation Patterns

Motion design patterns for Torale using Framer Motion. Animations should feel mechanical, precise, and purposeful.

## Core Principles

1. **The Machine is Alive** - Use motion to indicate system activity
2. **Mechanical Feel** - Snappy, precise movements with spring physics
3. **Sub-400ms** - Respect the Doherty Threshold for perceived performance
4. **Purpose Over Decoration** - Every animation must serve a functional purpose

## Required Dependency

```bash
npm install framer-motion
```

## The Three Core Motions

### 1. The "Snap" (Springs) - Layout Changes

Use for content appearing, filtering, or rearranging:

```typescript
import { motion } from 'framer-motion';

<motion.div
  layout
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, scale: 0.95 }}
  transition={{ type: "spring", stiffness: 300, damping: 25 }}
>
  {content}
</motion.div>
```

**When to use:**
- Grid items appearing/disappearing
- Sidebar opening/closing
- Filter results updating
- Cards being added/removed

### 2. The "Click" (Tap) - Buttons Feel Mechanical

Buttons should feel like physical switches:

```typescript
<motion.button
  whileTap={{ scale: 0.98, y: 1 }}
  className="bg-zinc-900 text-white px-5 py-2"
>
  Deploy
</motion.button>
```

**Enhanced with shadow:**
```typescript
<motion.button
  whileTap={{ scale: 0.98 }}
  className="bg-zinc-900 text-white px-5 py-2 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] active:translate-y-[2px] active:shadow-none"
>
  Deploy
</motion.button>
```

**When to use:**
- All clickable buttons
- Toggles and switches
- Interactive badges

### 3. The "Lift" (Hover) - Cards Indicate Interactivity

Cards should lift slightly on hover:

```typescript
<motion.div
  whileHover={{
    y: -2,
    boxShadow: "0 10px 30px -10px rgba(0,0,0,0.1)"
  }}
  transition={{ type: "spring", stiffness: 400, damping: 20 }}
  className="bg-white border border-zinc-200 p-6"
>
  {content}
</motion.div>
```

**When to use:**
- Dashboard cards
- Clickable list items
- Feature cards
- Any interactive surface

## Optimistic UI Updates

Show immediate feedback before API responds:

```typescript
import { useState } from 'react';
import { motion } from 'framer-motion';

function ToggleSwitch({ initialState }: { initialState: boolean }) {
  const [isActive, setIsActive] = useState(initialState);
  const [isLoading, setIsLoading] = useState(false);

  const handleToggle = async () => {
    // Immediate visual feedback
    setIsActive(!isActive);
    setIsLoading(true);

    try {
      // API call
      await updateMonitorStatus(!isActive);
    } catch (error) {
      // Rollback on error
      setIsActive(isActive);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.button
      onClick={handleToggle}
      className={`relative w-12 h-6 rounded-full transition-colors ${
        isActive ? 'bg-emerald-500' : 'bg-zinc-300'
      }`}
      whileTap={{ scale: 0.95 }}
    >
      <motion.div
        layout
        className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full shadow-sm"
        animate={{ x: isActive ? 24 : 0 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </motion.button>
  );
}
```

## System Pulse (Live Activity)

Show background work with pulsing indicators:

```typescript
// Status dot that pulses when active
<div className="flex items-center gap-2">
  <div className={`w-2 h-2 rounded-full ${
    isActive ? 'bg-emerald-500 animate-pulse' : 'bg-zinc-300'
  }`} />
  <span className="text-xs font-mono">
    {isActive ? 'Live' : 'Idle'}
  </span>
</div>
```

```typescript
// Badge with live indicator
<div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white border-2 border-zinc-900">
  <div className="w-2 h-2 bg-[hsl(10,90%,55%)] rounded-full animate-pulse" />
  <span className="text-xs font-mono font-bold uppercase">Incoming Signals</span>
</div>
```

## Staggered List Animations

Animate lists with staggered timing:

```typescript
import { motion, AnimatePresence } from 'framer-motion';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

function MonitorList({ monitors }) {
  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-4"
    >
      {monitors.map((monitor) => (
        <motion.div
          key={monitor.id}
          variants={item}
          className="bg-white border border-zinc-200 p-4"
        >
          {monitor.name}
        </motion.div>
      ))}
    </motion.div>
  );
}
```

## Scroll-Triggered Animations

Animate elements as they enter viewport:

```typescript
<motion.div
  initial={{ opacity: 0, y: 20 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-10%" }}
  transition={{ duration: 0.5 }}
>
  {content}
</motion.div>
```

**Stagger multiple sections:**
```typescript
<motion.div
  initial={{ opacity: 0, y: 20 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true }}
  transition={{ duration: 0.5, delay: index * 0.1 }}
>
  {content}
</motion.div>
```

## Page Transitions

Smooth transitions between views:

```typescript
import { AnimatePresence, motion } from 'framer-motion';

function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}

// Usage with routing
<AnimatePresence mode="wait">
  <PageTransition key={location.pathname}>
    {children}
  </PageTransition>
</AnimatePresence>
```

## Loading States

### Skeleton Loader
```typescript
<div className="animate-pulse space-y-4">
  <div className="h-4 bg-zinc-200 rounded w-3/4" />
  <div className="h-4 bg-zinc-200 rounded w-1/2" />
  <div className="h-4 bg-zinc-200 rounded w-5/6" />
</div>
```

### Spinner (Terminal Style)
```typescript
<div className="w-4 h-4 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin" />
```

### Progress Bar
```typescript
<motion.div
  className="h-2 bg-zinc-900"
  initial={{ width: 0 }}
  animate={{ width: `${progress}%` }}
  transition={{ duration: 0.3 }}
/>
```

## Modal/Dialog Entry

```typescript
import { motion, AnimatePresence } from 'framer-motion';

function Modal({ isOpen, onClose, children }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-6"
          >
            <div className="bg-white border-2 border-zinc-900 rounded-lg p-8 max-w-lg w-full">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
```

## Terminal Cursor

```typescript
<span className="inline-block w-2 h-5 bg-zinc-500 animate-pulse ml-1" />
```

## Live Event Stream

Animate incoming events:

```typescript
import { motion, AnimatePresence } from 'framer-motion';

function EventStream({ events }) {
  return (
    <div className="space-y-3">
      <AnimatePresence initial={false}>
        {events.map((event) => (
          <motion.div
            key={event.id}
            initial={{ opacity: 0, y: -30, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="bg-white p-4 border border-zinc-200"
          >
            {event.title}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
```

## Timing Reference

| Animation Type | Duration | Easing |
|----------------|----------|--------|
| Micro-interactions | 100-200ms | ease-out |
| Element transitions | 200-300ms | spring |
| Page transitions | 300-400ms | ease-in-out |
| Loading states | 400-600ms | linear |

## Anti-Patterns to Avoid

❌ Don't use slow, "smooth" transitions (>500ms)
❌ Don't animate for decoration only
❌ Don't use bounce/elastic easing (breaks "mechanical" feel)
❌ Don't animate everything - be selective
❌ Don't use continuous animations without purpose

## When to Apply This Skill

Use these patterns when:
- Building interactive components
- Creating page transitions
- Showing loading/loading states
- Indicating system activity
- Providing user feedback
- Building dashboard interfaces

## Performance Tips

1. Use `transform` and `opacity` for animations (GPU-accelerated)
2. Prefer `layout` prop for position changes
3. Use `will-change: transform` sparingly
4. Debounce rapid state changes
5. Use `AnimatePresence` for exit animations
