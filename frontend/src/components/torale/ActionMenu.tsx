import React from 'react';
import { MoreHorizontal } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { LucideIcon } from 'lucide-react';

/**
 * ActionMenu - Reusable action dropdown menu
 *
 * Used for:
 * - Task card actions (Edit, Run, Pause, Delete)
 * - Admin table row actions
 * - Any context menu with multiple actions
 */

export interface Action {
  id: string;
  label: string;
  icon: LucideIcon;
  onClick: () => void;
  variant?: 'default' | 'destructive';
  separator?: boolean; // Show separator before this action
}

interface ActionMenuProps {
  actions: Action[];
  triggerIcon?: LucideIcon;
  triggerClassName?: string;
}

export const ActionMenu: React.FC<ActionMenuProps> = ({
  actions,
  triggerIcon: TriggerIcon = MoreHorizontal,
  triggerClassName = 'text-zinc-400 hover:text-zinc-900 transition-colors',
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        asChild
        onClick={(e) => e.stopPropagation()}
      >
        <button className={triggerClassName}>
          <TriggerIcon className="w-4 h-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {actions.map((action, index) => {
          const Icon = action.icon;
          return (
            <React.Fragment key={action.id}>
              {action.separator && index > 0 && <DropdownMenuSeparator />}
              <DropdownMenuItem
                onClick={action.onClick}
                className={action.variant === 'destructive' ? 'text-destructive' : ''}
              >
                <Icon className="mr-2 h-4 w-4" />
                {action.label}
              </DropdownMenuItem>
            </React.Fragment>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
