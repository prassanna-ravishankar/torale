import React, { useState, useRef, useEffect } from 'react';
import { LucideIcon, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * FilterGroup - Data-driven filter button group
 *
 * Replaces repeated filter button patterns with consistent styling
 * Generic type T ensures type-safe filter IDs
 *
 * Responsive mode:
 * - Desktop: Horizontal tabs with labels and counts
 * - Mobile: Compact dropdown (select element styled to match design system)
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
  responsive?: boolean; // Auto-switch to dropdown on mobile
}

export const FilterGroup = <T extends string = string>({
  filters,
  active,
  onChange,
  className,
  responsive = false,
}: FilterGroupProps<T>) => {
  const activeFilter = filters.find((f) => f.id === active);

  // Desktop tabs (always shown if not responsive, or on md+ screens)
  const tabsContent = (
    <div className={cn('flex gap-2', responsive && 'hidden md:flex', className)}>
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

  // Mobile dropdown (only shown when responsive=true on small screens)
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const dropdownContent = responsive && (
    <div ref={dropdownRef} className={cn('relative md:hidden', className)}>
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between bg-white border-2 border-zinc-200 rounded-sm pl-3 pr-3 py-2 text-xs font-medium text-zinc-900 hover:border-zinc-400 transition-colors"
      >
        <span className="flex items-center gap-2">
          {activeFilter?.icon && <activeFilter.icon className="w-3 h-3" />}
          {activeFilter?.label}
          {activeFilter?.count !== undefined && ` (${activeFilter.count})`}
        </span>
        <ChevronDown className={cn('w-4 h-4 text-zinc-400 transition-transform', isOpen && 'rotate-180')} />
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border-2 border-zinc-900 rounded-sm shadow-brutalist z-50 max-h-60 overflow-auto">
          {filters.map((filter) => {
            const Icon = filter.icon;
            const isActive = active === filter.id;

            return (
              <button
                key={filter.id}
                onClick={() => {
                  onChange(filter.id);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full flex items-center gap-2 px-3 py-2.5 text-xs font-medium transition-colors text-left border-b border-zinc-100 last:border-b-0',
                  isActive
                    ? 'bg-zinc-900 text-white'
                    : 'text-zinc-900 hover:bg-zinc-50'
                )}
              >
                {Icon && <Icon className="w-3 h-3 flex-shrink-0" />}
                <span className="flex-1">
                  {filter.label}
                  {filter.count !== undefined && ` (${filter.count})`}
                </span>
                {isActive && <span className="text-lg">✓</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );

  return (
    <>
      {tabsContent}
      {dropdownContent}
    </>
  );
};
