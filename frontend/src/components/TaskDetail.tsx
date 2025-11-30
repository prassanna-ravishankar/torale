import React, { useState, useEffect, useCallback } from 'react'
import type { Task, TaskExecution } from '@/types'
import api from '@/lib/api'
import { toast } from 'sonner'
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { ExecutionTimeline } from "@/components/ExecutionTimeline";
import { StateComparison } from "@/components/StateComparison";
import { CronDisplay } from "@/components/ui/CronDisplay";
import { NotificationChannelBadges } from "@/components/notifications/NotificationChannelBadges";
import { getTaskStatus, TaskActivityState } from '@/lib/taskStatus';
import {
  ArrowLeft,
  Clock,
  Search,
  Bell,
  Play,
  Loader2,
  Trash2,
  Mail,
  Webhook,
  Activity,
  CheckCircle,
  Pause,
} from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface TaskDetailProps {
  taskId: string;
  onBack: () => void;
  onDeleted: () => void;
}

export const TaskDetail: React.FC<TaskDetailProps> = ({
  taskId,
  onBack,
  onDeleted,
}) => {
  const [task, setTask] = useState<Task | null>(null);
  const [executions, setExecutions] = useState<TaskExecution[]>([]);
  const [notifications, setNotifications] = useState<TaskExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);
  const [activeTab, setActiveTab] = useState("executions");

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [taskData, executionsData, notificationsData] = await Promise.all([
        api.getTask(taskId),
        api.getTaskExecutions(taskId),
        api.getTaskNotifications(taskId),
      ]);
      setTask(taskData);
      setExecutions(executionsData);
      setNotifications(notificationsData);
    } catch (error) {
      console.error("Failed to load task details:", error);
      toast.error('Failed to load task details');
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleToggle = async () => {
    if (!task) return;
    try {
      await api.updateTask(taskId, { is_active: !task.is_active });
      await loadData();
      toast.success(task.is_active ? 'Task paused' : 'Task activated');
    } catch (error) {
      console.error("Failed to toggle task:", error);
      toast.error('Failed to update task');
    }
  };

  const handleExecute = async () => {
    setIsExecuting(true);
    try {
      await api.executeTask(taskId);
      toast.success('Task execution started');
      await loadData();
    } catch (error) {
      console.error("Failed to execute task:", error);
      toast.error('Failed to execute task');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.deleteTask(taskId);
      toast.success('Task deleted');
      onDeleted();
    } catch (error) {
      console.error("Failed to delete task:", error);
      toast.error('Failed to delete task');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!task) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground mb-4">Task not found</p>
        <Button onClick={onBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
      </div>
    );
  }

  // Get task status from centralized logic
  const status = getTaskStatus(task.is_active, task.last_execution?.condition_met);

  // Map icon name to Lucide icon component
  const StatusIcon = {
    Activity,
    CheckCircle,
    Pause,
  }[status.iconName];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4 flex-1">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h1>{task.name}</h1>
              <Badge
                variant={
                  status.activityState === TaskActivityState.ACTIVE
                    ? 'default'
                    : status.activityState === TaskActivityState.COMPLETED
                    ? 'default'
                    : 'secondary'
                }
                className="flex items-center gap-1"
              >
                <StatusIcon className="h-3 w-3" />
                {status.label}
              </Badge>
            </div>
            <p className="text-muted-foreground">{task.search_query}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleExecute}
            disabled={isExecuting}
          >
            {isExecuting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            Run Now
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="icon">
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Task</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to delete "{task.name}"? This action cannot be
                  undone. All execution history will be permanently deleted.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock className="h-4 w-4" />
              <p>Schedule</p>
            </div>
          </CardHeader>
          <CardContent>
            <CronDisplay cron={task.schedule} className="text-sm" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Search className="h-4 w-4" />
              <p>Trigger Condition</p>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{task.condition_description}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Bell className="h-4 w-4" />
              <p>When to Notify</p>
            </div>
          </CardHeader>
          <CardContent>
            <p className="capitalize text-sm">
              {task.notify_behavior === 'once' && 'Once only'}
              {task.notify_behavior === 'always' && 'Every time'}
              {task.notify_behavior === 'track_state' && 'On changes'}
            </p>
            <div className="flex items-center gap-2 mt-3">
              <Switch
                checked={task.is_active}
                onCheckedChange={handleToggle}
                className="data-[state=unchecked]:bg-muted data-[state=unchecked]:border-border"
              />
              <span className={`text-sm ${task.is_active ? 'text-muted-foreground' : 'font-medium'}`}>
                {task.is_active ? "Active" : "Paused - Click to resume"}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Mail className="h-4 w-4" />
              <p>Notification Channels</p>
            </div>
          </CardHeader>
          <CardContent>
            {task.notification_channels && task.notification_channels.length > 0 ? (
              <div className="space-y-3">
                <NotificationChannelBadges
                  channels={task.notification_channels}
                  notificationEmail={task.notification_email}
                  webhookUrl={task.webhook_url}
                />
                <div className="space-y-1 text-xs text-muted-foreground">
                  {task.notification_channels.includes('email') && (
                    <div className="flex items-start gap-1.5">
                      <Mail className="h-3 w-3 mt-0.5 shrink-0" />
                      <span className="truncate">
                        {task.notification_email || 'Default (Clerk email)'}
                      </span>
                    </div>
                  )}
                  {task.notification_channels.includes('webhook') && (
                    <div className="flex items-start gap-1.5">
                      <Webhook className="h-3 w-3 mt-0.5 shrink-0" />
                      <span className="truncate">
                        {task.webhook_url || 'Default webhook'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No channels configured</p>
            )}
          </CardContent>
        </Card>
      </div>

      {task.last_known_state && (
        <Card>
          <CardHeader>
            <h3>Last Known State</h3>
          </CardHeader>
          <CardContent>
            <div className="text-sm space-y-2">
              {Object.entries(task.last_known_state).map(([key, value]) => (
                <div key={key} className="flex items-start gap-2">
                  <span className="font-medium min-w-[150px]">{key}:</span>
                  <span className="text-muted-foreground">
                    {typeof value === "object" ? JSON.stringify(value, null, 2) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="executions">
            All Executions ({executions.length})
          </TabsTrigger>
          <TabsTrigger value="notifications">
            Notifications ({notifications.length})
          </TabsTrigger>
          <TabsTrigger value="changes">State Changes</TabsTrigger>
        </TabsList>

        <TabsContent value="executions" className="mt-6">
          <ExecutionTimeline executions={executions} />
        </TabsContent>

        <TabsContent value="notifications" className="mt-6">
          <ExecutionTimeline
            executions={notifications}
            highlightNotifications={true}
          />
        </TabsContent>

        <TabsContent value="changes" className="mt-6">
          <StateComparison executions={executions} />
        </TabsContent>
      </Tabs>
    </div>
  );
};
