import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * FilterGroup - Data-driven filter button group
 *
 * Replaces repeated filter button patterns with consistent styling
 */

export interface FilterOption {
  id: string;
  label: string;
  count?: number;
  icon?: LucideIcon;
}

interface FilterGroupProps {
  filters: FilterOption[];
  active: string;
  onChange: (filterId: string) => void;
  className?: string;
}

export const FilterGroup: React.FC<FilterGroupProps> = ({
  filters,
  active,
  onChange,
  className,
}) => {
  return (
    <div className={cn('flex gap-2', className)}>
      {filters.map((filter) => {
        const Icon = filter.icon;
        const isActive = active === filter.id;

        return (
          <button
            key={filter.id}
            onClick={() => onChange(filter.id)}
            className={cn(
              'px-3 py-1.5 border border-zinc-200 rounded-sm text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-2',
              isActive
                ? 'bg-zinc-900 text-white border-zinc-900'
                : 'bg-white text-zinc-600 hover:border-zinc-400'
            )}
          >
            {Icon && <Icon className="w-3 h-3" />}
            {filter.label}
            {filter.count !== undefined && ` (${filter.count})`}
          </button>
        );
      })}
    </div>
  );
};
