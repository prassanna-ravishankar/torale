import React, { useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Play, Pause, Trash2, Zap, ChevronRight, Settings } from 'lucide-react';
import { getTaskExecuteLabel } from '@/lib/utils';
import type { Task } from '@/types';

interface TaskActionsProps {
  task: Task;
  view: 'mobile' | 'desktop';
  onExecute: (taskId: string) => void;
  onToggle: (taskId: string, newState: 'active' | 'paused') => void;
  onEdit: (taskId: string) => void;
  onDelete: (taskId: string) => void;
  onViewDetails?: (taskId: string) => void;
}

export const TaskActions: React.FC<TaskActionsProps> = ({
  task,
  view,
  onExecute,
  onToggle,
  onEdit,
  onDelete,
  onViewDetails,
}) => {
  const isTaskActive = task.state === 'active';
  const isMobile = view === 'mobile';
  const iconSize = isMobile ? 'w-4 h-4' : 'w-3 h-3';
  const iconMargin = isMobile ? '' : 'mr-1.5';

  // Determine Run Once button configuration based on task state
  const runOnceConfig = useMemo(() => {
    const text = getTaskExecuteLabel(task.state, isMobile);

    switch (task.state) {
      case 'active':
        return {
          text,
          tooltip: 'Test the task immediately without waiting for the schedule',
          variant: 'default' as const,
        };
      case 'paused':
        return {
          text,
          tooltip: 'Test the task (currently paused) - will remain paused after execution',
          variant: 'secondary' as const,
        };
      case 'completed':
        return {
          text,
          tooltip: 'Test the completed task again - will remain completed',
          variant: 'outline' as const,
        };
      default:
        // Fallback for unexpected state values - treat as active for safety
        console.warn(`Unexpected task state: ${task.state}`);
        return {
          text,
          tooltip: 'Test the task immediately',
          variant: 'default' as const,
        };
    }
  }, [task.state, isMobile]);

  // Memoized event handlers for better performance
  const handleExecute = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onExecute(task.id);
  }, [onExecute, task.id]);

  const handleToggle = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onToggle(task.id, isTaskActive ? 'paused' : 'active');
  }, [onToggle, task.id, isTaskActive]);

  const handleEdit = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(task.id);
  }, [onEdit, task.id]);

  const handleDelete = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(task.id);
  }, [onDelete, task.id]);

  const handleViewDetails = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    onViewDetails?.(task.id);
  }, [onViewDetails, task.id]);

  if (isMobile) {
    // Mobile view - compact with icon-only buttons for edit/delete
    return (
      <div className="flex items-center gap-2 flex-wrap">
        <Button
          variant={runOnceConfig.variant}
          size="sm"
          onClick={handleExecute}
          title={runOnceConfig.tooltip}
          className="gap-1.5"
        >
          <Zap className={iconSize} />
          <span>{runOnceConfig.text}</span>
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={handleToggle}
          title={isTaskActive ? 'Pause' : 'Resume'}
          className="gap-1.5"
        >
          {isTaskActive ? (
            <>
              <Pause className={iconSize} />
              <span>Pause</span>
            </>
          ) : (
            <>
              <Play className={iconSize} />
              <span>Resume</span>
            </>
          )}
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={handleEdit}
          title="Edit"
          aria-label="Edit task"
        >
          <Settings className={iconSize} />
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={handleDelete}
          title="Delete"
          aria-label="Delete task"
          className="text-destructive hover:text-destructive hover:bg-destructive/10"
        >
          <Trash2 className={iconSize} />
        </Button>

        {onViewDetails && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleViewDetails}
            title="View Details"
            aria-label="View task details"
          >
            <ChevronRight className={iconSize} />
          </Button>
        )}
      </div>
    );
  }

  // Desktop view - full labels
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Button
        variant={runOnceConfig.variant}
        size="sm"
        onClick={handleExecute}
        title={runOnceConfig.tooltip}
      >
        <Zap className={`${iconSize} ${iconMargin}`} />
        {runOnceConfig.text}
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={handleToggle}
      >
        {isTaskActive ? (
          <>
            <Pause className={`${iconSize} ${iconMargin}`} />
            Pause
          </>
        ) : (
          <>
            <Play className={`${iconSize} ${iconMargin}`} />
            Resume
          </>
        )}
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={handleEdit}
      >
        <Settings className={`${iconSize} ${iconMargin}`} />
        Edit
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={handleDelete}
        className="text-destructive hover:text-destructive hover:bg-destructive/10"
      >
        <Trash2 className={`${iconSize} ${iconMargin}`} />
        Delete
      </Button>

      {onViewDetails && (
        <Button
          variant="outline"
          size="sm"
          onClick={handleViewDetails}
        >
          View Details
          <ChevronRight className={`${iconSize} ml-1.5`} />
        </Button>
      )}
    </div>
  );
};