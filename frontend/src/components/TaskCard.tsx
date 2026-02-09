import React, { useState } from 'react';
import type { Task } from '@/types';
import { StatusBadge, SectionLabel, ActionMenu, BrutalistCard, type Action } from '@/components/torale';
import { Clock, Globe, Trash2, Play, Edit, Pause, Zap } from 'lucide-react';
import { getTaskStatus } from '@/lib/taskStatus';
import { formatTimeAgo, formatTimeUntil, getTaskExecuteLabel } from '@/lib/utils';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

/**
 * TaskCard - Signal Card design from MockDashboard.tsx
 * Mission Control style card with brutalist aesthetics
 */

interface TaskCardProps {
  task: Task;
  onToggle: (id: string, newState: 'active' | 'paused') => void;
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
  const status = getTaskStatus(task.state);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const isTaskActive = task.state === 'active';

  const handleDelete = (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    onDelete(task.id);
    setShowDeleteDialog(false);
  };

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
      label: getTaskExecuteLabel(task.state),
      icon: Zap,
      onClick: () => onExecute(task.id),
    },
    {
      id: 'toggle',
      label: isTaskActive ? 'Pause Monitoring' : 'Resume Monitoring',
      icon: isTaskActive ? Pause : Play,
      onClick: () => onToggle(task.id, isTaskActive ? 'paused' : 'active'),
      separator: true,
    },
    {
      id: 'delete',
      label: 'Delete',
      icon: Trash2,
      onClick: () => setShowDeleteDialog(true),
      variant: 'destructive',
    },
  ];

  const handleQuickToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle(task.id, isTaskActive ? 'paused' : 'active');
  };

  return (
    <BrutalistCard
      variant="clickable"
      animate={true}
      hoverEffect={true}
      onClick={() => {
        // Prevent navigation if delete dialog is open
        if (showDeleteDialog) return;
        onClick(task.id);
      }}
      className="group relative"
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
            title={isTaskActive ? 'Pause Monitoring' : 'Resume Monitoring'}
          >
            {isTaskActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <ActionMenu actions={actions} />
        </div>
      </div>

      {/* Middle: Last Check + Next Check */}
      <div className="p-4 flex-1 flex gap-6">
        <div>
          <SectionLabel className="mb-1">Last Check</SectionLabel>
          <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-600">
            <Clock className="w-3 h-3" />
            {task.last_execution?.started_at
              ? formatTimeAgo(task.last_execution.started_at)
              : 'Not run yet'}
          </div>
        </div>
        <div>
          <SectionLabel className="mb-1">Next Check</SectionLabel>
          <div className="flex items-center gap-1.5 text-xs font-mono text-zinc-600">
            <Clock className="w-3 h-3" />
            {task.next_run ? formatTimeUntil(task.next_run) : '—'}
          </div>
        </div>
      </div>

      {/* Bottom: Footer with Status */}
      <div className="bg-zinc-50 p-3 border-t border-zinc-100 flex justify-between items-center">
        <StatusBadge variant={status.activityState} />
        <span className="text-[10px] text-zinc-400 font-mono">
          {task.last_execution?.completed_at
            ? `Run: ${new Date(task.last_execution.completed_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}`
            : 'Not run yet'}
        </span>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent className="border-2 border-zinc-900 shadow-brutalist-lg">
          <AlertDialogHeader className="border-b-2 border-zinc-100 pb-4">
            <AlertDialogTitle className="font-grotesk">Delete Monitor</AlertDialogTitle>
            <AlertDialogDescription className="text-zinc-500">
              Are you sure you want to delete "{task.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-3">
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="shadow-brutalist">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </BrutalistCard>
  );
};
