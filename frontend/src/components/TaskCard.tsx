import React from 'react';
import { motion } from '@/lib/motion-compat';
import type { Task } from '@/types';
import { Button } from '@/components/ui/button';
import {
  Clock,
  Globe,
  MoreHorizontal,
  Trash2,
  Play,
  Edit,
  Pause,
  Activity,
  PauseCircle,
  AlertCircle,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { CronDisplay } from '@/components/ui/CronDisplay';
import { getTaskStatus, TaskActivityState } from '@/lib/taskStatus';

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

// Status Badge Component (from MockDashboard lines 92-113)
const StatusBadge = ({ status }: { status: TaskActivityState }) => {
  const config = {
    [TaskActivityState.ACTIVE]: {
      bg: 'bg-emerald-50',
      text: 'text-emerald-600',
      border: 'border-emerald-200',
      icon: <Activity className="w-3 h-3" />,
      label: 'Active'
    },
    [TaskActivityState.PAUSED]: {
      bg: 'bg-zinc-50',
      text: 'text-zinc-500',
      border: 'border-zinc-200',
      icon: <PauseCircle className="w-3 h-3" />,
      label: 'Paused'
    },
    [TaskActivityState.COMPLETED]: {
      bg: 'bg-blue-50',
      text: 'text-blue-600',
      border: 'border-blue-200',
      icon: <Activity className="w-3 h-3" />,
      label: 'Completed'
    },
  }[status] || {
    bg: 'bg-amber-50',
    text: 'text-amber-600',
    border: 'border-amber-200',
    icon: <AlertCircle className="w-3 h-3" />,
    label: 'Unknown'
  };

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-sm border text-[10px] font-mono uppercase tracking-wider ${config.bg} ${config.text} ${config.border}`}>
      {config.icon}
      {config.label}
    </div>
  );
};

export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onToggle,
  onDelete,
  onExecute,
  onEdit,
  onClick,
}) => {
  const status = getTaskStatus(task.is_active, task.last_execution?.condition_met);

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle(task.id, !task.is_active);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete "${task.name}"?`)) {
      onDelete(task.id);
    }
  };

  const handleExecute = (e: React.MouseEvent) => {
    e.stopPropagation();
    onExecute(task.id);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(task.id);
  };

  // Calculate success rate (mock data for now)
  const successRate = 99.8;

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
        <div className="flex gap-2">
          <div className="p-2 bg-zinc-50 border border-zinc-100 rounded-sm text-zinc-500 group-hover:text-zinc-900 group-hover:border-zinc-300 transition-colors">
            <Globe className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-zinc-900 font-grotesk leading-tight mb-1">
              {task.name}
            </h3>
            <div className="flex items-center gap-2 text-[10px] text-zinc-400 font-mono">
              <span className="truncate max-w-[180px]">{task.search_query}</span>
            </div>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <button className="text-zinc-400 hover:text-zinc-900 transition-colors">
              <MoreHorizontal className="w-4 h-4" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleEdit}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleExecute}>
              <Play className="mr-2 h-4 w-4" />
              Run Now
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleToggle}>
              {task.is_active ? (
                <>
                  <Pause className="mr-2 h-4 w-4" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Resume
                </>
              )}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleDelete} className="text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Middle: Metrics */}
      <div className="p-4 grid grid-cols-2 gap-4 flex-1">
        <div>
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">Schedule</div>
          <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-600">
            <Clock className="w-3 h-3" />
            <CronDisplay cron={task.schedule} className="text-xs font-mono" />
          </div>
        </div>
        <div>
          <div className="text-[10px] text-zinc-400 uppercase tracking-wider mb-1">Uptime</div>
          <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-600">
            <div className={`w-1.5 h-1.5 rounded-full ${successRate > 99 ? 'bg-emerald-500' : 'bg-amber-500'}`} />
            {successRate}%
          </div>
        </div>
      </div>

      {/* Bottom: Footer with Status */}
      <div className="bg-zinc-50 p-3 border-t border-zinc-100 flex justify-between items-center">
        <StatusBadge status={status.activityState} />
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
