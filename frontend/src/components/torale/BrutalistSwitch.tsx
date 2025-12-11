import React from 'react';
import * as SwitchPrimitive from '@radix-ui/react-switch';
import { cn } from '@/lib/utils';

interface BrutalistSwitchProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
}

/**
 * BrutalistSwitch - A brutalist-styled toggle switch
 *
 * Follows Torale design system:
 * - Thick borders (border-2)
 * - Zinc color palette
 * - Minimal rounded corners
 * - Clear checked/unchecked states
 */
export const BrutalistSwitch: React.FC<BrutalistSwitchProps> = ({
  checked,
  onCheckedChange,
  disabled = false,
  className,
}) => {
  return (
    <SwitchPrimitive.Root
      checked={checked}
      onCheckedChange={onCheckedChange}
      disabled={disabled}
      className={cn(
        'inline-flex h-6 w-11 shrink-0 items-center border-2 transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900 focus-visible:ring-offset-2',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'rounded-sm', // Minimal rounding for brutalist style
        checked
          ? 'bg-emerald-500 border-emerald-600' // Checked state: emerald (matches active badges)
          : 'bg-zinc-100 border-zinc-300', // Unchecked state: subtle zinc
        className
      )}
    >
      <SwitchPrimitive.Thumb
        className={cn(
          'pointer-events-none block h-4 w-4 border-2 bg-white transition-transform',
          'rounded-[1px]', // Very minimal rounding
          checked
            ? 'translate-x-[22px] border-emerald-700'
            : 'translate-x-[2px] border-zinc-400'
        )}
      />
    </SwitchPrimitive.Root>
  );
};
