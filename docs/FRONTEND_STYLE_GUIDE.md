# Frontend Style Guide

## Design System

### Component Library
Torale uses **shadcn/ui** components with **Tailwind CSS** for styling. All components follow a consistent design language with thoughtful spacing, color usage, and interaction patterns.

### Icons
- **Primary Icon Library**: [lucide-react](https://lucide.dev/)
- **Usage**: Import icons from `lucide-react` for consistent iconography across the app
- **No Emojis**: Avoid using emoji icons in UI components - use lucide icons instead for a modern, professional look
- **Icon Sizes**:
  - Small: `h-3 w-3` (12px)
  - Default: `h-4 w-4` (16px)
  - Medium: `h-5 w-5` (20px)
  - Large: `h-6 w-6` (24px)

**Example Icon Usage:**
```tsx
import { Music, Gamepad2, Bot } from "lucide-react";

// In a card with background
<div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
  <Music className="h-4 w-4 text-primary" />
</div>
```

### Color Palette

#### Semantic Colors
- **Primary**: Purple accent - used for primary actions, active states, and key UI elements
- **Accent**: Secondary highlights
- **Muted**: Subdued text and backgrounds (`text-muted-foreground`)
- **Destructive**: Error states and delete actions

#### Opacity Levels
- `/10` - Very subtle backgrounds (e.g., `bg-primary/10`)
- `/15` - Hover state intensification (e.g., `group-hover:bg-primary/15`)
- `/50` - Medium transparency for icons (e.g., `text-muted-foreground/50`)
- `/70` - Secondary text (e.g., `text-foreground/70`)
- `/80` - Muted foreground text

### Typography

#### Headings
- **Page Title**: `text-2xl font-bold tracking-tight`
- **Card Title**: `text-sm font-semibold` or `text-base font-bold`
- **Section Title**: `text-lg font-bold`

#### Body Text
- **Primary**: `text-sm` or `text-base`
- **Secondary/Description**: `text-[10px]` or `text-xs` with `text-muted-foreground`
- **Labels**: `text-xs font-medium` or `text-[9px] font-semibold uppercase tracking-wide`

#### Line Heights
- **Tight**: `leading-tight` - for titles
- **Snug**: `leading-snug` - for compact descriptions
- **Relaxed**: `leading-relaxed` - for readable body text

#### Text Truncation
- Single line: `truncate`
- Two lines: `line-clamp-2`

### Spacing

#### Container Padding
- **Modal/Dialog Content**: `p-3` or `p-6`
- **Card Header**: `p-3` to `pb-2` or `pb-3`
- **Card Content**: `px-3 py-2`
- **Container**: `px-4`

#### Gaps
- **Tight**: `gap-2` (8px)
- **Default**: `gap-3` (12px) or `gap-4` (16px)
- **Spacious**: `gap-6` (24px)

#### Vertical Spacing
- **Tight**: `space-y-2`
- **Default**: `space-y-4`
- **Sections**: `space-y-6`

### Layout Patterns

#### Modals & Dialogs

**Size Guidelines:**
- Template selection modal: `max-w-5xl` (1024px)
- Standard forms: `max-w-4xl` (896px)
- Compact wizards: `max-w-3xl` (768px)

**Structure:**
```tsx
<DialogContent className="max-w-5xl overflow-hidden flex flex-col">
  <DialogHeader className="space-y-2 pb-4 flex-shrink-0">
    {/* Header content */}
  </DialogHeader>

  <div className="flex-1 overflow-y-auto min-h-0">
    {/* Scrollable content */}
  </div>

  <DialogFooter className="flex-shrink-0 pt-4 border-t gap-2">
    {/* Footer actions */}
  </DialogFooter>
</DialogContent>
```

#### Grids

**Template Cards:**
```tsx
<div className="grid grid-cols-3 gap-3">
  {/* 3-column grid with tight gaps */}
</div>
```

**Responsive Grids:**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Responsive grid: 1 col on mobile, 2 on tablet, 3 on desktop */}
</div>
```

### Interactive Elements

#### Cards

**Clickable Card:**
```tsx
<Card className="cursor-pointer transition-all duration-200 hover:border-primary hover:shadow-sm group relative overflow-hidden">
  <div className="absolute inset-0 bg-gradient-to-br from-primary/3 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
  <CardHeader className="p-3 relative">
    {/* Card content */}
  </CardHeader>
</Card>
```

**Key Patterns:**
- Use `group` for coordinated hover effects
- Subtle gradient overlays on hover (`from-primary/3`)
- Border color change on hover (`hover:border-primary`)
- Minimal shadow increase (`hover:shadow-sm`)

#### Buttons

**Size Variants:**
- Small: `size="sm"` - for compact actions
- Default: No size prop
- Icon-only: Use consistent icon sizes with padding

**Common Patterns:**
```tsx
// Primary action
<Button className="gap-2">
  <CheckCircle2 className="h-4 w-4" />
  Create Task
</Button>

// Ghost variant with icon
<Button variant="ghost" className="gap-2">
  <Sparkles className="h-4 w-4" />
  Start from Scratch
</Button>
```

#### Separators

**With Centered Text:**
```tsx
<div className="flex items-center gap-3">
  <Separator className="flex-1" />
  <span className="text-sm text-muted-foreground">Or start from scratch</span>
  <Separator className="flex-1" />
</div>
```

### Icon Containers

**Rounded Square with Background:**
```tsx
<div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/15 transition-colors">
  <IconComponent className="h-4 w-4 text-primary" />
</div>
```

**Sizes:**
- Small: `h-6 w-6` container, `h-3 w-3` icon
- Default: `h-8 w-8` container, `h-4 w-4` icon
- Medium: `h-10 w-10` container, `h-5 w-5` icon

### Animations & Transitions

**Standard Durations:**
- Fast: `duration-200` (200ms)
- Default: No duration specified (uses CSS default)

**Common Transition Properties:**
- Colors: `transition-colors`
- All: `transition-all duration-200`
- Opacity: `transition-opacity`

### Best Practices

#### 1. Consistent Icon Usage
✅ **Do:**
```tsx
import { Music } from "lucide-react";
<Music className="h-4 w-4 text-primary" />
```

❌ **Don't:**
```tsx
<span>🎵</span> // No emojis as icons
```

#### 2. Proper Text Hierarchy
✅ **Do:**
```tsx
<CardTitle className="text-sm font-semibold">
  Title
</CardTitle>
<CardDescription className="text-[10px] text-muted-foreground">
  Description
</CardDescription>
```

❌ **Don't:**
```tsx
<div className="text-lg">Title</div> // Inconsistent sizing
<p className="text-sm">Description</p> // Missing muted styling
```

#### 3. Hover Effects
✅ **Do:**
```tsx
<Card className="group hover:border-primary transition-colors">
  <div className="group-hover:bg-primary/15 transition-colors">
    {/* Content */}
  </div>
</Card>
```

❌ **Don't:**
```tsx
<Card className="hover:scale-110"> // Too aggressive
  {/* Content */}
</Card>
```

#### 4. Spacing Consistency
✅ **Do:**
```tsx
<div className="space-y-4"> // Use Tailwind spacing utilities
  <div>Item 1</div>
  <div>Item 2</div>
</div>
```

❌ **Don't:**
```tsx
<div>
  <div style={{ marginBottom: '13px' }}>Item 1</div> // Custom values
  <div>Item 2</div>
</div>
```

### Component Patterns

#### Template Card Pattern
```tsx
{templates.map((template) => {
  const IconComponent = getTemplateIcon(template.name);
  return (
    <Card
      key={template.id}
      className="cursor-pointer transition-all duration-200 hover:border-primary hover:shadow-sm group relative overflow-hidden"
      onClick={() => handleTemplateSelect(template.id)}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/3 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <CardHeader className="p-3 relative">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/15 transition-colors">
            <IconComponent className="h-4 w-4 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <CardTitle className="text-sm font-semibold group-hover:text-primary transition-colors leading-tight mb-0.5">
              {template.name}
            </CardTitle>
            <CardDescription className="text-[10px] leading-snug text-muted-foreground/70 line-clamp-2">
              {template.description}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
    </Card>
  );
})}
```

#### Dialog with Scroll Pattern
```tsx
<DialogContent className="max-w-5xl overflow-hidden flex flex-col">
  <DialogHeader className="space-y-2 pb-4 flex-shrink-0">
    <DialogTitle className="text-2xl font-bold tracking-tight">
      Title
    </DialogTitle>
    <DialogDescription className="text-sm text-muted-foreground">
      Description
    </DialogDescription>
  </DialogHeader>

  <div className="flex-1 overflow-y-auto min-h-0">
    <form className="space-y-6 p-1">
      {/* Form content */}
    </form>
  </div>

  <DialogFooter className="flex-shrink-0 pt-4 border-t gap-2">
    <Button variant="outline">Cancel</Button>
    <Button>Submit</Button>
  </DialogFooter>
</DialogContent>
```

## Code Style

### Import Organization
```tsx
// 1. React imports
import React, { useState, useEffect } from "react";

// 2. External libraries
import { useNavigate } from "react-router-dom";

// 3. UI components
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

// 4. Icons
import { Search, Bell, Clock } from "lucide-react";

// 5. Local components and utilities
import { TaskCard } from "@/components/TaskCard";
import api from "@/lib/api";
import { cn } from "@/lib/utils";

// 6. Types
import type { Task, NotifyBehavior } from "@/types";
```

### Component Structure
```tsx
interface ComponentProps {
  // Props interface
}

export const Component: React.FC<ComponentProps> = ({
  prop1,
  prop2,
}) => {
  // 1. Hooks
  const [state, setState] = useState();

  // 2. Event handlers
  const handleClick = () => {
    // ...
  };

  // 3. Render
  return (
    <div>
      {/* Component JSX */}
    </div>
  );
};
```

### Utility Functions
Place helper functions outside components when they don't need closure over component state:

```tsx
// Helper function outside component
const getTemplateIcon = (templateName: string) => {
  // ...
};

export const Component: React.FC = () => {
  // Component implementation
};
```

## Accessibility

- Use semantic HTML elements
- Include `aria-label` for icon-only buttons
- Ensure proper color contrast ratios
- Test keyboard navigation
- Use `sr-only` class for screen reader text when needed

## Performance

- Use `React.memo()` for expensive list items
- Implement proper key props in lists
- Avoid inline function definitions in render when possible
- Use `line-clamp-*` instead of JavaScript text truncation
