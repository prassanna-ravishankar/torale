---
name: torale-design-patterns
description: Core implementation patterns for Torale's design system. Covers AnimatePresence with motion components, dialog consistency (AlertDialog over window.confirm), design tokens, type-safe generics, map objects over ternaries, avoiding component shadowing, and direct pass-through. Includes anti-patterns and best practices with examples.
---

# Torale Design System - Implementation Patterns

Core implementation patterns and principles for building with the Torale neo-brutalist design system.

## 1. AnimatePresence + Motion Components

**Pattern**: AnimatePresence requires direct children to be motion components for enter/exit animations.

**❌ Wrong**:
```tsx
<AnimatePresence>
  {items.map(item => (
    <BrutalistTableRow key={item.id}>  {/* Regular component */}
      {/* ... */}
    </BrutalistTableRow>
  ))}
</AnimatePresence>
```

**✅ Right**:
```tsx
// 1. Make component accept motion props
interface BrutalistTableRowProps extends Omit<MotionProps, 'onClick'> {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}

export const BrutalistTableRow = ({ children, onClick, className, ...motionProps }: BrutalistTableRowProps) => {
  return (
    <motion.tr onClick={onClick} className={cn(/* ... */)} {...motionProps}>
      {children}
    </motion.tr>
  );
};

// 2. Pass animation props
<AnimatePresence>
  {items.map(item => (
    <BrutalistTableRow
      key={item.id}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* ... */}
    </BrutalistTableRow>
  ))}
</AnimatePresence>
```

**Why**: Framer Motion's AnimatePresence tracks motion components to apply animations. Regular components break the animation chain.

---

## 2. Dialog Consistency

**Pattern**: Always use custom AlertDialog, never window.confirm() or window.alert().

**❌ Wrong**:
```tsx
onClick={() => {
  if (confirm('Are you sure you want to delete this?')) {
    handleDelete(id);
  }
}}
```

**✅ Right**:
```tsx
const [showDeleteDialog, setShowDeleteDialog] = useState(false);

// In actions
onClick={() => setShowDeleteDialog(true)}

// Dialog
<AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
  <AlertDialogContent className="border-2 border-zinc-900 shadow-brutalist-lg">
    <AlertDialogHeader className="border-b-2 border-zinc-100 pb-4">
      <AlertDialogTitle className="font-grotesk">Delete Monitor</AlertDialogTitle>
      <AlertDialogDescription className="text-zinc-500">
        Are you sure you want to delete "{itemName}"? This action cannot be undone.
      </AlertDialogDescription>
    </AlertDialogHeader>
    <AlertDialogFooter className="gap-3">
      <AlertDialogCancel>Cancel</AlertDialogCancel>
      <AlertDialogAction onClick={handleDelete} className="shadow-brutalist">
        Delete
      </AlertDialogAction>
    </AlertDialogFooter>
  </AlertDialogContent>
</AlertDialog>
```

**Why**: Native browser dialogs cannot be styled to match the design system. Custom dialogs maintain visual consistency and provide better UX.

---

## 3. Design Tokens Over Hardcoded Values

**Pattern**: Define brand colors and design tokens in tailwind.config.js, not inline.

**❌ Wrong**:
```tsx
<ExternalLink className="text-zinc-400 hover:text-[hsl(10,90%,55%)]" />
```

**✅ Right**:
```js
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        brand: {
          orange: "hsl(10, 90%, 55%)",
        },
      },
    },
  },
}
```

```tsx
<ExternalLink className="text-zinc-400 hover:text-brand-orange" />
```

**Why**: Single source of truth for design tokens. Easy to update brand colors globally. Better autocomplete and type safety.

---

## 4. Type-Safe Generic Components

**Pattern**: Use TypeScript generics for data-driven components to ensure type safety.

**❌ Wrong**:
```tsx
// Component accepts any string
interface FilterGroupProps {
  active: string;
  onChange: (id: string) => void;
}

// Usage requires type assertion
<FilterGroup
  active={activeFilter}
  onChange={(id) => setActiveFilter(id as 'all' | 'active' | 'paused')}
/>
```

**✅ Right**:
```tsx
// Component is generic over filter ID type
interface FilterGroupProps<T extends string = string> {
  filters: FilterOption<T>[];
  active: T;
  onChange: (filterId: T) => void;
}

export const FilterGroup = <T extends string = string>({
  filters,
  active,
  onChange,
}: FilterGroupProps<T>) => {
  // ...
};

// Usage is type-safe
<FilterGroup<'all' | 'active' | 'paused'>
  active={activeFilter}
  onChange={setActiveFilter}  // No type assertion needed!
/>
```

**Why**: Eliminates type assertions, provides better autocomplete, catches type errors at compile time.

---

## 5. Map Objects Over Nested Ternaries

**Pattern**: Use map objects for status/enum mappings instead of nested ternary operators.

**❌ Wrong**:
```tsx
<StatusBadge variant={
  status === 'COMPLETED' ? 'completed' :
  status === 'FAILED' ? 'failed' :
  status === 'RUNNING' ? 'running' : 'unknown'
} />
```

**✅ Right**:
```tsx
const statusMap = {
  COMPLETED: 'completed',
  FAILED: 'failed',
  RUNNING: 'running',
} as const;

<StatusBadge variant={statusMap[status] || 'unknown'} />
```

**Why**: More readable, easier to extend with new statuses, single source of truth for mapping logic.

---

## 6. Avoid Component Shadowing

**Pattern**: Prevent local components from shadowing imported shared components.

**❌ Wrong**:
```tsx
import { StatusBadge } from '@/components/torale';

// Local component shadows imported one!
const StatusBadge = ({ status }: { status: string }) => {
  // Custom implementation
};

// Uses local version instead of shared component
<StatusBadge status={item.status} />
```

**✅ Right**:
```tsx
import { StatusBadge, type StatusVariant } from '@/components/torale';

// Helper function instead of shadowing component
const getStatusVariant = (status: string): StatusVariant => {
  switch (status) {
    case 'success': return 'completed';
    case 'failed': return 'failed';
    default: return 'unknown';
  }
};

// Uses shared component
<StatusBadge variant={getStatusVariant(item.status)} />
```

**Why**: Ensures consistency across the app. Prevents accidental divergence from design system. Easier to maintain.

---

## 7. Direct Pass-Through When Types Align

**Pattern**: When data types already match component API, pass values directly instead of transforming.

**❌ Wrong**:
```tsx
// status.activityState is already 'active' | 'completed' | 'paused'
<StatusBadge variant={
  status.activityState === 'active' ? 'active' :
  status.activityState === 'completed' ? 'completed' : 'paused'
} />
```

**✅ Right**:
```tsx
<StatusBadge variant={status.activityState} />
```

**Why**: Simpler code, leverages TypeScript's type system, fewer opportunities for bugs.

---

## General Principles

1. **Rely on Component Defaults**: Check parent component capabilities before adding custom styling (e.g., BrutalistCard's built-in hover effects)

2. **Semantic HTML**: Use semantic elements for interactive content:
   - Clickable areas → `<button>` not `<div onClick>`
   - Links → `<a>` not `<span onClick>`
   - Forms → proper `<form>`, `<input>`, `<label>` elements

3. **Accessibility First**:
   - Provide ARIA labels where needed
   - Ensure keyboard navigation works
   - Use semantic motion components for screen readers

4. **Import Hygiene**:
   - Import shared components, don't redefine locally
   - Use type imports (`import type`) for TypeScript types
   - Group imports: React → Third-party → Local

## Related Skills

- `torale-design-system.md` - Component reference and API documentation
- `CLAUDE.md` - Project overview and architecture
