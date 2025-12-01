import React from 'react';
import type { Task } from '@/types';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Clock,
  Search,
  MoreVertical,
  Trash2,
  Play,
  Edit,
  ExternalLink,
  Pause,
  Activity,
  CheckCircle,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { CronDisplay } from '@/components/ui/CronDisplay';
import { NotificationChannelBadges } from '@/components/notifications/NotificationChannelBadges';
import { cn } from '@/lib/utils';
import { getTaskStatus, TaskActivityState } from '@/lib/taskStatus';

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
  // Get task status from centralized logic
  const status = getTaskStatus(task.is_active, task.last_execution?.condition_met);

  // Map icon name to Lucide icon component
  const StatusIcon = {
    Activity,
    CheckCircle,
    Pause,
  }[status.iconName];

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

  return (
    <Card
      className={cn(
        'cursor-pointer hover:border-primary transition-all',
        !task.is_active && 'opacity-60'
      )}
      onClick={() => onClick(task.id)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <h3 className="font-semibold truncate">{task.name}</h3>
              <Badge
                variant={
                  status.activityState === TaskActivityState.ACTIVE
                    ? 'default'
                    : status.activityState === TaskActivityState.COMPLETED
                    ? 'default'
                    : 'secondary'
                }
                className="shrink-0 flex items-center gap-1"
              >
                <StatusIcon className="h-3 w-3" />
                {status.label}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2">
              &ldquo;{task.search_query}&rdquo;
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-2 pb-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4 shrink-0" />
          <CronDisplay cron={task.schedule} className="text-xs" />
        </div>

        {task.notification_channels && task.notification_channels.length > 0 && (
          <NotificationChannelBadges
            channels={task.notification_channels}
            notificationEmail={task.notification_email}
            webhookUrl={task.webhook_url}
          />
        )}

        {status.activityState === TaskActivityState.COMPLETED && (
          <div className="p-2.5 bg-blue-500/5 rounded-md border border-blue-500/20">
            <p className="text-xs text-blue-600 dark:text-blue-400">
              ✓ {status.description} - click to view details
            </p>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex items-center gap-2 pt-3 border-t">
        {/* Play Button - Prominent */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleExecute}
          className="flex-1"
        >
          <Play className="h-4 w-4 mr-2" />
          Run
        </Button>

        {/* Edit Button - Prominent */}
        <Button
          variant="outline"
          size="sm"
          onClick={handleEdit}
          className="flex-1"
        >
          <Edit className="h-4 w-4 mr-2" />
          Edit
        </Button>

        {/* More Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
            <Button variant="ghost" size="icon" className="shrink-0">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handleToggle}>
              {task.is_active ? (
                <>
                  <Pause className="mr-2 h-4 w-4" />
                  Pause Task
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Resume Task
                </>
              )}
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation();
                onClick(task.id);
              }}
            >
              <ExternalLink className="mr-2 h-4 w-4" />
              View Details
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleDelete} className="text-destructive">
              <Trash2 className="mr-2 h-4 w-4" />
              Delete Task
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardFooter>
    </Card>
  );
};
