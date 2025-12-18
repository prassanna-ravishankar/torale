import React from 'react';
import { Button } from '@/components/ui/button';
import { Play, Pause, Trash2, Zap, ChevronRight, Settings } from 'lucide-react';
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

  // Determine Run Once button text and tooltip based on task state
  const getRunOnceConfig = () => {
    switch (task.state) {
      case 'active':
        return {
          text: isMobile ? 'Test' : 'Run Once',
          tooltip: 'Test the task immediately without waiting for the schedule',
          variant: 'default' as const,
        };
      case 'paused':
        return {
          text: isMobile ? 'Test' : 'Run Once',
          tooltip: 'Test the task (currently paused) - will remain paused after execution',
          variant: 'secondary' as const,
        };
      case 'completed':
        return {
          text: isMobile ? 'Re-test' : 'Run Again',
          tooltip: 'Test the completed task again - will remain completed',
          variant: 'outline' as const,
        };
      default:
        return {
          text: isMobile ? 'Test' : 'Run Once',
          tooltip: 'Test the task immediately',
          variant: 'default' as const,
        };
    }
  };

  const runOnceConfig = getRunOnceConfig();

  const handleAction = (e: React.MouseEvent, action: () => void) => {
    e.stopPropagation();
    action();
  };

  if (isMobile) {
    // Mobile view - compact with icon-only buttons for edit/delete
    return (
      <div className="flex items-center gap-2 flex-wrap">
        <Button
          variant={runOnceConfig.variant}
          size="sm"
          onClick={(e) => handleAction(e, () => onExecute(task.id))}
          title={runOnceConfig.tooltip}
          className="gap-1.5"
        >
          <Zap className={iconSize} />
          <span>{runOnceConfig.text}</span>
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={(e) => handleAction(e, () => onToggle(task.id, isTaskActive ? 'paused' : 'active'))}
          title={isTaskActive ? 'Pause Schedule' : 'Start Schedule'}
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
              <span>Start</span>
            </>
          )}
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={(e) => handleAction(e, () => onEdit(task.id))}
          title="Edit"
        >
          <Settings className={iconSize} />
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={(e) => handleAction(e, () => onDelete(task.id))}
          title="Delete"
          className="text-destructive hover:text-destructive"
        >
          <Trash2 className={iconSize} />
        </Button>

        {onViewDetails && (
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => handleAction(e, () => onViewDetails(task.id))}
            title="View Details"
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
        onClick={(e) => handleAction(e, () => onExecute(task.id))}
        title={runOnceConfig.tooltip}
      >
        <Zap className={`${iconSize} ${iconMargin}`} />
        {runOnceConfig.text}
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={(e) => handleAction(e, () => onToggle(task.id, isTaskActive ? 'paused' : 'active'))}
      >
        {isTaskActive ? (
          <>
            <Pause className={`${iconSize} ${iconMargin}`} />
            Pause Schedule
          </>
        ) : (
          <>
            <Play className={`${iconSize} ${iconMargin}`} />
            Start Schedule
          </>
        )}
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={(e) => handleAction(e, () => onEdit(task.id))}
      >
        <Settings className={`${iconSize} ${iconMargin}`} />
        Edit
      </Button>

      <Button
        variant="outline"
        size="sm"
        onClick={(e) => handleAction(e, () => onDelete(task.id))}
        className="text-destructive hover:text-destructive"
      >
        <Trash2 className={`${iconSize} ${iconMargin}`} />
        Delete
      </Button>

      {onViewDetails && (
        <Button
          variant="outline"
          size="sm"
          onClick={(e) => handleAction(e, () => onViewDetails(task.id))}
        >
          View Details
          <ChevronRight className={`${iconSize} ml-1.5`} />
        </Button>
      )}
    </div>
  );
};