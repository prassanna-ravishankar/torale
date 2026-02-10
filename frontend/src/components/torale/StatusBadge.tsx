import React from 'react';
import {
  Activity,
  CheckCircle,
  CheckCircle2,
  Pause,
  PauseCircle,
  AlertCircle,
  Clock,
  XCircle,
  Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * StatusBadge - Unified status indicator for tasks, executions, and activity states
 *
 * Supports all status types found across the application:
 * - Task activity: active, paused, completed
 * - Execution status: success, failed, pending, running
 * - Condition status: met, not_met
 * - Custom status with icon
 */

export type StatusVariant =
  | 'active'
  | 'paused'
  | 'completed'
  | 'success'
  | 'failed'
  | 'pending'
  | 'running'
  | 'retrying'
  | 'triggered'
  | 'cancelled'
  | 'unknown';

interface StatusBadgeProps {
  variant: StatusVariant;
  label?: string;
  icon?: React.ReactNode;
  className?: string;
  size?: 'sm' | 'md';
}

const variantConfig: Record<
  StatusVariant,
  {
    bg: string;
    text: string;
    border: string;
    icon: React.ReactNode;
    label: string;
  }
> = {
  active: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-600',
    border: 'border-emerald-200',
    icon: <Activity className="w-3 h-3" />,
    label: 'Active',
  },
  paused: {
    bg: 'bg-zinc-50',
    text: 'text-zinc-500',
    border: 'border-zinc-200',
    icon: <PauseCircle className="w-3 h-3" />,
    label: 'Paused',
  },
  completed: {
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    border: 'border-blue-200',
    icon: <CheckCircle className="w-3 h-3" />,
    label: 'Completed',
  },
  success: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
    icon: <CheckCircle2 className="h-3 w-3" />,
    label: 'Success',
  },
  failed: {
    bg: 'bg-red-50',
    text: 'text-red-700',
    border: 'border-red-200',
    icon: <XCircle className="h-3 w-3" />,
    label: 'Failed',
  },
  pending: {
    bg: 'bg-zinc-50',
    text: 'text-zinc-600',
    border: 'border-zinc-200',
    icon: <Clock className="h-3 w-3" />,
    label: 'Pending',
  },
  running: {
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    border: 'border-amber-200',
    icon: <Clock className="h-3 w-3" />,
    label: 'Running',
  },
  retrying: {
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    border: 'border-amber-200',
    icon: <Clock className="h-3 w-3" />,
    label: 'Retrying',
  },
  triggered: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
    icon: <Zap className="h-3 w-3" />,
    label: 'Triggered',
  },
  cancelled: {
    bg: 'bg-zinc-50',
    text: 'text-zinc-500',
    border: 'border-zinc-200',
    icon: <Pause className="h-3 w-3" />,
    label: 'Cancelled',
  },
  unknown: {
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    border: 'border-amber-200',
    icon: <AlertCircle className="h-3 w-3" />,
    label: 'Unknown',
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  variant,
  label,
  icon,
  className,
  size = 'sm',
}) => {
  const config = variantConfig[variant];
  const displayLabel = label || config.label;
  const displayIcon = icon || config.icon;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-1 rounded-sm border font-mono uppercase tracking-wider',
        config.bg,
        config.text,
        config.border,
        size === 'sm' ? 'text-[9px]' : 'text-[10px]',
        className
      )}
    >
      {displayIcon}
      {displayLabel}
    </span>
  );
};
