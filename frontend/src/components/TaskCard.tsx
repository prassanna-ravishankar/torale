import React from 'react';
import { motion } from '@/lib/motion-compat';
import type { Task } from '@/types';
import { StatusBadge, SectionLabel, ActionMenu, type Action } from '@/components/torale';
import { Clock, Globe, Trash2, Play, Edit, Pause } from 'lucide-react';
import { CronDisplay } from '@/components/ui/CronDisplay';
import { getTaskStatus } from '@/lib/taskStatus';

/**
 * TaskCard - Signal Card design from MockDashboard.tsx
 * Mission Control style card with brutalist aesthetics
 */

interface TaskCardProps {
  task: Task;
  onToggle: (id: string, isActive: boolean) => void;
  onDelete: (id: string) => void;
  onExecute: (id: string) => void;
  onEdit: (id: string) => void;
  onClick: (id: string) => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onToggle,
  onDelete,
  onExecute,
  onEdit,
  onClick,
}) => {
  const status = getTaskStatus(task.is_active, task.last_execution?.condition_met);
  const successRate = 99.8;

  // Build actions array for ActionMenu
  const actions: Action[] = [
    {
      id: 'edit',
      label: 'Edit',
      icon: Edit,
      onClick: () => onEdit(task.id),
    },
    {
      id: 'execute',
      label: 'Run Now',
      icon: Play,
      onClick: () => onExecute(task.id),
    },
    {
      id: 'toggle',
      label: task.is_active ? 'Pause' : 'Resume',
      icon: task.is_active ? Pause : Play,
      onClick: () => onToggle(task.id, !task.is_active),
      separator: true,
    },
    {
      id: 'delete',
      label: 'Delete',
      icon: Trash2,
      onClick: () => {
        if (confirm(`Are you sure you want to delete "${task.name}"?`)) {
          onDelete(task.id);
        }
      },
      variant: 'destructive',
    },
  ];

  const handleQuickToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle(task.id, !task.is_active);
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ y: -2, boxShadow: "0 10px 30px -10px rgba(0,0,0,0.1)" }}
      className="bg-white border border-zinc-200 group relative flex flex-col cursor-pointer"
      onClick={() => onClick(task.id)}
    >
      {/* Top Bar: Icon + Name + Actions */}
      <div className="p-4 border-b border-zinc-100 flex justify-between items-start">
        <div className="flex gap-2 flex-1 min-w-0">
          <div className="p-2 bg-zinc-50 border border-zinc-100 rounded-sm text-zinc-500 group-hover:text-zinc-900 group-hover:border-zinc-300 transition-colors">
            <Globe className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-bold text-sm text-zinc-900 font-grotesk leading-tight mb-1">
              {task.name}
            </h3>
            <div className="flex items-center gap-2 text-[10px] text-zinc-400 font-mono">
              <span className="truncate">{task.search_query}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 ml-2">
          {/* Quick pause/unpause button - User Feedback #5 */}
          <button
            onClick={handleQuickToggle}
            className="p-1.5 text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 rounded-sm transition-colors"
            title={task.is_active ? 'Pause monitor' : 'Resume monitor'}
          >
            {task.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <ActionMenu actions={actions} />
        </div>
      </div>

      {/* Middle: Metrics */}
      <div className="p-4 grid grid-cols-2 gap-4 flex-1">
        <div>
          <SectionLabel className="mb-1">Schedule</SectionLabel>
          <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-600">
            <Clock className="w-3 h-3" />
            <CronDisplay cron={task.schedule} className="text-xs font-mono" />
          </div>
        </div>
        <div>
          <SectionLabel className="mb-1">Uptime</SectionLabel>
          <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-600">
            <div className={`w-1.5 h-1.5 rounded-full ${successRate > 99 ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            {successRate}%
          </div>
        </div>
      </div>

      {/* Bottom: Footer with Status */}
      <div className="bg-zinc-50 p-3 border-t border-zinc-100 flex justify-between items-center">
        <StatusBadge
          variant={
            status.activityState === 'active'
              ? 'active'
              : status.activityState === 'completed'
              ? 'completed'
              : 'paused'
          }
        />
        <span className="text-[10px] text-zinc-400 font-mono">
          {task.last_execution?.completed_at
            ? `Run: ${new Date(task.last_execution.completed_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}`
            : 'Not run yet'}
        </span>
      </div>

      {/* Hover Selection Border */}
      <div className="absolute inset-0 border-2 border-transparent group-hover:border-zinc-900 pointer-events-none transition-colors" />
    </motion.div>
  );
};
