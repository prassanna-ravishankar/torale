---
name: torale-design-patterns
description: Core implementation patterns for Torale's brutalist design system. Focuses on critical anti-patterns to avoid (AnimatePresence motion chains, component shadowing, native dialogs) and key principles (type safety, responsive components, design tokens). Teaches decision-making over exhaustive examples.
---

# Torale Design System - Implementation Patterns

Critical patterns and anti-patterns for building with the Torale neo-brutalist design system.

## 1. AnimatePresence Requires Motion Components

**Why it matters**: AnimatePresence can't track exit animations on regular components.

**❌ Wrong**: Using regular components as direct children
```tsx
<AnimatePresence>
  {items.map(item => (
    <BrutalistTableRow key={item.id}>{/* ... */}</BrutalistTableRow>
  ))}
</AnimatePresence>
```

**✅ Right**: Component accepts and spreads motion props
```tsx
interface BrutalistTableRowProps extends Omit<MotionProps, 'onClick'> {
  children: React.ReactNode;
}

export const BrutalistTableRow = ({ children, ...motionProps }) => (
  <motion.tr {...motionProps}>{children}</motion.tr>
);

<AnimatePresence>
  {items.map(item => (
    <BrutalistTableRow
      key={item.id}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    />
  ))}
</AnimatePresence>
```

## 2. Never Use Native Dialogs

**Why it matters**: Native browser dialogs can't be styled to match the design system.

**❌ Wrong**: `window.confirm()` or `window.alert()`
```tsx
if (confirm('Delete this?')) { handleDelete(); }
```

**✅ Right**: Custom AlertDialog with brutalist styling
```tsx
const [showDialog, setShowDialog] = useState(false);

<AlertDialog open={showDialog} onOpenChange={setShowDialog}>
  <AlertDialogContent className="border-2 border-zinc-900 shadow-brutalist-lg">
    {/* ... */}
  </AlertDialogContent>
</AlertDialog>
```

## 3. Design Tokens Over Hardcoded Values

**Why it matters**: Single source of truth for brand colors enables global updates.

**❌ Wrong**: Inline color values
```tsx
className="hover:text-[hsl(10,90%,55%)]"
```

**✅ Right**: Named tokens in `tailwind.config.js`
```tsx
// tailwind.config.js
colors: { brand: { orange: "hsl(10, 90%, 55%)" } }

// Usage
className="hover:text-brand-orange"
```

## 4. Type-Safe Generics

**Why it matters**: Eliminates type assertions and catches errors at compile time.

**❌ Wrong**: Accepting `string` and requiring type assertions
```tsx
onChange: (id: string) => void

// Usage requires manual casting
onChange={(id) => setFilter(id as FilterType)}
```

**✅ Right**: Generic over allowed values
```tsx
interface Props<T extends string> {
  active: T;
  onChange: (id: T) => void;
}

// Usage is type-safe
<FilterGroup<'all' | 'active' | 'paused'>
  onChange={setFilter}  // No casting needed
/>
```

## 5. Map Objects Over Nested Ternaries

**Why it matters**: More readable, easier to extend, single source of truth.

**❌ Wrong**: Nested ternary chains
```tsx
variant={status === 'COMPLETED' ? 'completed' : status === 'FAILED' ? 'failed' : 'unknown'}
```

**✅ Right**: Map object with fallback
```tsx
const statusMap = {
  COMPLETED: 'completed',
  FAILED: 'failed',
  RUNNING: 'running',
} as const;

variant={statusMap[status] || 'unknown'}
```

## 6. Don't Shadow Shared Components

**Why it matters**: Prevents accidental divergence from design system.

**❌ Wrong**: Local component shadows import
```tsx
import { StatusBadge } from '@/components/torale';

const StatusBadge = ({ status }) => { /* custom */ };  // Shadows import!
```

**✅ Right**: Helper function instead
```tsx
import { StatusBadge, type StatusVariant } from '@/components/torale';

const getStatusVariant = (status: string): StatusVariant => {
  // Mapping logic
};

<StatusBadge variant={getStatusVariant(status)} />
```

## 7. Direct Pass-Through When Types Align

**Why it matters**: Simpler code, leverages TypeScript's type system.

**❌ Wrong**: Unnecessary transformation
```tsx
// status.activityState is already 'active' | 'completed' | 'paused'
variant={status.activityState === 'active' ? 'active' : 'completed'}
```

**✅ Right**: Direct pass-through
```tsx
variant={status.activityState}
```

## 8. Build Responsive Behavior Into Components

**Why it matters**: Solves mobile issues once, ensures consistency everywhere.

**❌ Wrong**: Duplicating responsive logic at every usage site
```tsx
// Every usage duplicates this
<div className="hidden md:flex">
  {filters.map(f => <button>{f.label}</button>)}
</div>
<select className="md:hidden">
  {filters.map(f => <option>{f.label}</option>)}
</select>
```

**✅ Right**: Component handles responsive internally
```tsx
// Component implements responsive prop
<FilterGroup responsive={true} filters={filters} />

// Implementation (in component):
const tabs = <div className={cn('flex gap-2', responsive && 'hidden md:flex')}>...</div>
const dropdown = responsive && <div className="md:hidden">...</div>
return <>{tabs}{dropdown}</>
```

## General Principles

**Semantic HTML**: Use `<button>` for clicks, `<a>` for links, proper form elements

**Accessibility**: Provide ARIA labels, ensure keyboard navigation works

**Import Hygiene**: Import shared components, use type imports for types

**Component Defaults**: Check what parent component already provides before adding custom styling

## Related Skills

- `torale-component-library.md` - When to use shared components vs building custom
- `CLAUDE.md` - Full project architecture and design system
