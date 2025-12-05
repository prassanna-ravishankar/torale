import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * SectionLabel - Consistent section header labels
 *
 * Standard brutalist design system label:
 * - 10px font-mono uppercase
 * - Zinc-400 text color
 * - Wide letter spacing
 * - Optional icon
 */

interface SectionLabelProps {
  children: React.ReactNode;
  icon?: LucideIcon;
  className?: string;
}

export const SectionLabel: React.FC<SectionLabelProps> = ({
  children,
  icon: Icon,
  className,
}) => {
  return (
    <div
      className={cn(
        'flex items-center gap-2 text-[10px] font-mono uppercase tracking-wider text-zinc-400',
        className
      )}
    >
      {Icon && <Icon className="h-4 w-4" />}
      {children}
    </div>
  );
};
