import React from 'react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { SectionLabel } from './SectionLabel';

/**
 * CollapsibleSection - Unified collapsible section with consistent trigger styling
 *
 * Used for:
 * - Task configuration sections
 * - Execution metadata
 * - Dev/debug information
 */

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  defaultOpen?: boolean;
  variant?: 'default' | 'dark' | 'mobile';
  className?: string;
  triggerClassName?: string;
  contentClassName?: string;
}

export const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  children,
  open,
  onOpenChange,
  defaultOpen,
  variant = 'default',
  className,
  triggerClassName,
  contentClassName,
}) => {
  const [isOpen, setIsOpen] = React.useState(defaultOpen ?? false);
  const controlled = open !== undefined;
  const expanded = controlled ? open : isOpen;

  const handleOpenChange = (newOpen: boolean) => {
    if (!controlled) {
      setIsOpen(newOpen);
    }
    onOpenChange?.(newOpen);
  };

  const triggerStyles = {
    default:
      'flex items-center gap-2 text-sm font-mono text-zinc-500 hover:text-zinc-900 transition-colors w-full justify-between p-3 bg-white border-2 border-zinc-200',
    dark: 'flex items-center gap-2 text-sm font-mono text-zinc-500 hover:text-zinc-900 transition-colors w-full justify-between p-3 bg-zinc-900 border border-zinc-800',
    mobile:
      'flex items-center gap-2 text-sm font-mono text-zinc-500 hover:text-zinc-900 transition-colors w-full justify-between p-3 bg-white border-2 border-zinc-200 lg:hidden',
  };

  return (
    <Collapsible
      open={expanded}
      onOpenChange={handleOpenChange}
      className={className}
    >
      <CollapsibleTrigger
        className={cn(triggerStyles[variant], triggerClassName)}
      >
        <SectionLabel className="text-zinc-500">
          {title}
        </SectionLabel>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-zinc-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-zinc-500" />
        )}
      </CollapsibleTrigger>
      <CollapsibleContent className={contentClassName}>
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
};
