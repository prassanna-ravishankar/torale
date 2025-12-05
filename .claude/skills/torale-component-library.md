---
name: torale-component-library
description: Principles for using Torale's shared component library (@/components/torale). Teaches when to use shared components vs building custom, how to discover what's available, and design system consistency over exhaustive API documentation.
---

# Torale Component Library - Usage Principles

## Core Principle: Import, Don't Copy

**Before creating any component, check if it exists in `@/components/torale`.**

```bash
# Find shared components
ls frontend/src/components/torale/

# Search for similar patterns
rg "export const.*=" frontend/src/components/torale/
```

## Available Shared Components

The following components exist in `@/components/torale`:

- **StatusBadge** - Status indicators (handles all task states)
- **BrutalistCard** - Card containers with hover effects
- **BrutalistTable** - Table components (Table, Header, Body, Row, Head, Cell)
- **ActionMenu** - Dropdown menus with actions
- **FilterGroup** - Type-safe filter tabs (supports responsive mobile dropdown)
- **EmptyState** - Empty states with optional actions
- **SectionLabel** - Section headers
- **CollapsibleSection** - Collapsible sections

**Read the source** to understand props and capabilities - components are well-typed and documented.

## Decision Framework

### ✅ Use Shared Components When:
- A component exists that matches your use case
- You need a common pattern (status, filters, tables, cards)
- Visual consistency with design system matters
- The component is reusable across pages

### ❌ Create Custom When:
- No shared component exists for your use case
- The pattern is truly unique to one feature
- Forcing a shared component would require heavy customization

### 🔄 Improve Shared Components When:
- You need a variant that could benefit other features
- Missing prop would make component more flexible
- Pattern could be generalized

**Don't create local variants - improve the shared component instead.**

## Common Anti-Patterns

### ❌ Shadowing Shared Components
```tsx
import { StatusBadge } from '@/components/torale';

// DON'T: Redefine component locally
const StatusBadge = ({ status }) => { /* custom */ };
```

### ❌ Copy-Pasting from Skills
```tsx
// DON'T: Copy component code from docs
const MyStatusBadge = () => {
  return <div className="px-2 py-1 bg-green-500">...</div>
};

// DO: Import and use
import { StatusBadge } from '@/components/torale';
<StatusBadge variant="active" />
```

### ❌ Reinventing Existing Patterns
```tsx
// DON'T: Build custom filter tabs
<div className="flex gap-2">
  {filters.map(f => <button>{f.label}</button>)}
</div>

// DO: Use FilterGroup (type-safe, responsive, tested)
<FilterGroup filters={filters} active={active} onChange={onChange} />
```

## Key Design System Patterns

### Type-Safe Generics
Many components use TypeScript generics for type safety:

```tsx
// FilterGroup infers types from filter IDs
<FilterGroup<'all' | 'active' | 'paused'>
  filters={[...]}
  active={activeFilter}
  onChange={setActiveFilter}  // No type assertions needed
/>
```

### Responsive Props
Components handle responsive behavior internally:

```tsx
// FilterGroup automatically switches to dropdown on mobile
<FilterGroup responsive={true} {...props} />
```

### Motion Props
Animation-capable components accept motion props:

```tsx
<BrutalistTableRow
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
  exit={{ opacity: 0 }}
>
  {content}
</BrutalistTableRow>
```

## How to Discover Component Capabilities

1. **Read the source**: Components are in `frontend/src/components/torale/`
2. **Check TypeScript types**: Props interfaces are exported
3. **Search usage**: `rg "StatusBadge" frontend/src/` shows real examples
4. **Ask**: If unsure whether to use shared vs custom, ask

## When Building New Components

If you determine a new component is needed:

1. **Consider if it belongs in shared library** - Will other features use it?
2. **Follow brutalist design patterns** - See `torale-design-patterns.md`
3. **Make it type-safe** - Use TypeScript generics where appropriate
4. **Support motion props** - If used in animated contexts
5. **Document usage** - Add to this list if it becomes shared

## Related Skills

- `torale-design-patterns.md` - Implementation patterns and anti-patterns
- `CLAUDE.md` - Full project architecture and design system overview
