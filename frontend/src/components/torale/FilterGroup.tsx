import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * FilterGroup - Data-driven filter button group
 *
 * Replaces repeated filter button patterns with consistent styling
 * Generic type T ensures type-safe filter IDs
 */

export interface FilterOption<T extends string = string> {
  id: T;
  label: string;
  count?: number;
  icon?: LucideIcon;
}

interface FilterGroupProps<T extends string = string> {
  filters: FilterOption<T>[];
  active: T;
  onChange: (filterId: T) => void;
  className?: string;
}

export const FilterGroup = <T extends string = string>({
  filters,
  active,
  onChange,
  className,
}: FilterGroupProps<T>) => {
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
