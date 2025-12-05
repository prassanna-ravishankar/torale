import React from 'react';
import { motion } from '@/lib/motion-compat';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * EmptyState - Consistent empty state component
 *
 * Used for:
 * - No monitors/tasks
 * - No executions
 * - No notifications
 * - Empty search results
 */

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
  className,
}) => {
  const commonContent = (
    <>
      <div className="w-12 h-12 rounded-full bg-zinc-50 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
        <Icon className="w-6 h-6" />
      </div>
      <span className="font-mono text-xs uppercase tracking-widest font-bold">
        {title}
      </span>
      {description && (
        <p className="text-xs text-zinc-500 mt-2 max-w-md text-center">
          {description}
        </p>
      )}
    </>
  );

  if (action) {
    return (
      <motion.button
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        onClick={action.onClick}
        className={cn(
          'w-full border-2 border-dashed border-zinc-200 rounded-sm flex flex-col items-center justify-center p-12 text-zinc-400 transition-all min-h-[200px]',
          'hover:border-zinc-400 hover:text-zinc-600 cursor-pointer group',
          className
        )}
      >
        {commonContent}
      </motion.button>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn(
        'w-full border-2 border-dashed border-zinc-200 rounded-sm flex flex-col items-center justify-center p-12 text-zinc-400 transition-all min-h-[200px]',
        className
      )}
    >
      {commonContent}
    </motion.div>
  );
};
