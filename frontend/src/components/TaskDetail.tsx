import React, { useState, useEffect, useCallback } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import type { Task, TaskExecution } from '@/types'
import api from '@/lib/api'
import { toast } from 'sonner'
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InfoCard, CollapsibleSection, StatusBadge } from "@/components/torale";
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
  Check,
  X,
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
  const [searchParams, setSearchParams] = useSearchParams();
  const isJustCreated = searchParams.get('justCreated') === 'true';
  const tabFromUrl = searchParams.get('tab') as 'executions' | 'notifications' | 'changes' | null;

  const [task, setTask] = useState<Task | null>(null);
  const [executions, setExecutions] = useState<TaskExecution[]>([]);
  const [notifications, setNotifications] = useState<TaskExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);
  const [activeTab, setActiveTab] = useState<string>(tabFromUrl || "executions");
  const [configExpanded, setConfigExpanded] = useState(false);
  const [lastKnownStateExpanded, setLastKnownStateExpanded] = useState(false);

  const loadData = useCallback(async (skipLoadingState = false) => {
    if (!skipLoadingState) {
      setIsLoading(true);
    }
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
      if (!skipLoadingState) {
        setIsLoading(false);
      }
    }
  }, [taskId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Sync activeTab to URL
  useEffect(() => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      if (activeTab !== 'executions') {
        newParams.set('tab', activeTab);
      } else {
        newParams.delete('tab');
      }
      return newParams;
    }, { replace: true });
  }, [activeTab, setSearchParams]);

  // Auto-refresh executions while first execution is pending/running (for just-created tasks)
  useEffect(() => {
    if (!isJustCreated || !task) return;

    const firstExecution = executions[0];
    const isFirstExecutionRunning =
      executions.length === 0 ||
      (firstExecution && ['pending', 'running'].includes(firstExecution.status));

    if (isFirstExecutionRunning) {
      const interval = setInterval(() => {
        loadData(true); // Skip loading state to prevent page flashing
      }, 3000); // Refresh every 3 seconds

      return () => clearInterval(interval);
    }
  }, [isJustCreated, task, executions, loadData]);

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

  const firstExecution = executions[0];
  const isFirstExecutionComplete = firstExecution?.status === 'success';

  const handleDismissBanner = () => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      newParams.delete('justCreated');
      return newParams;
    });
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto p-8">
      {/* Breadcrumb */}
      <div className="font-mono text-xs text-zinc-400 mb-4">
        <a href="/dashboard" className="hover:text-zinc-900 transition-colors">Monitors</a>
        {' / '}
        <span className="text-zinc-900">{task.name}</span>
      </div>

      {/* Just Created Banner */}
      {isJustCreated && (
        <div className="bg-emerald-50 p-6 border-2 border-emerald-200 animate-in fade-in slide-in-from-top-4 duration-500">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-start gap-3 flex-1">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                <Check className="h-5 w-5 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold tracking-tight">
                  Task successfully created
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Monitoring: <span className="text-foreground font-medium">{task.search_query}</span>
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDismissBanner}
              className="shrink-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Progress indicators */}
          <div className="space-y-3 mb-6">
            <div className="flex items-center gap-3">
              <Check className="h-4 w-4 text-primary shrink-0" />
              <span className="text-sm text-muted-foreground">Task initialized</span>
            </div>
            <div className="flex items-center gap-3">
              {isFirstExecutionComplete ? (
                <Check className="h-4 w-4 text-primary shrink-0" />
              ) : (
                <Loader2 className="h-4 w-4 text-muted-foreground animate-spin shrink-0" />
              )}
              <span className="text-sm text-muted-foreground">
                First check {isFirstExecutionComplete ? 'complete' : 'running...'}
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="text-sm text-muted-foreground">
                Welcome email arriving shortly
              </span>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="text-sm text-muted-foreground">
                Next check: <CronDisplay cron={task.schedule} className="inline" />
              </span>
            </div>
          </div>

          {/* What to expect */}
          <div className="pt-6 border-t border-border/50">
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
              What to Expect
            </h4>
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <Mail className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                <p className="text-sm text-muted-foreground">
                  Welcome email with first check results and task details
                </p>
              </div>
              <div className="flex items-start gap-2">
                <Clock className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                <p className="text-sm text-muted-foreground">
                  Automated checks <CronDisplay cron={task.schedule} className="inline lowercase" />
                </p>
              </div>
              <div className="flex items-start gap-2">
                <Bell className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                <p className="text-sm text-muted-foreground">
                  {task.notify_behavior === 'once' && 'Email when condition is met, then monitoring stops'}
                  {task.notify_behavior === 'always' && 'Email every time condition is met'}
                  {task.notify_behavior === 'track_state' && 'Email only when information changes'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header Section */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-4">
          <Link to="/dashboard">
            <Button variant="ghost" size="icon" className="shrink-0">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <h1 className="font-grotesk text-2xl md:text-4xl font-bold truncate">{task.name}</h1>
              <StatusBadge
                variant={
                  status.activityState === 'active'
                    ? 'active'
                    : status.activityState === 'completed'
                    ? 'completed'
                    : 'paused'
                }
              />
            </div>
            <p className="text-zinc-500 text-sm truncate">{task.search_query}</p>
          </div>
        </div>

        {/* Action Buttons - Stack on mobile */}
        <div className="flex items-center gap-2 flex-wrap mb-6 lg:mb-8">
          <Button
            variant="outline"
            onClick={handleExecute}
            disabled={isExecuting}
            size="sm"
          >
            {isExecuting ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            <span className="hidden sm:inline">Run Now</span>
            <span className="sm:hidden">Run</span>
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Trash2 className="h-4 w-4 sm:mr-2" />
                <span className="hidden sm:inline">Delete</span>
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent className="border-2 border-zinc-900 shadow-brutalist-lg">
              <AlertDialogHeader className="border-b-2 border-zinc-100 pb-4">
                <AlertDialogTitle className="font-grotesk">Delete Monitor</AlertDialogTitle>
                <AlertDialogDescription className="text-zinc-500">
                  Are you sure you want to delete "{task.name}"? This action cannot be
                  undone. All execution history will be permanently deleted.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter className="gap-3">
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete} className="shadow-brutalist">Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      {/* Task Configuration - Collapsible on Mobile, Always Visible on Desktop */}
      <CollapsibleSection
        title="Task Configuration"
        open={configExpanded}
        onOpenChange={setConfigExpanded}
        variant="mobile"
        className="lg:contents"
        contentClassName="lg:contents"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <InfoCard icon={Clock} label="Schedule">
            <CronDisplay cron={task.schedule} className="text-sm font-mono text-zinc-700" />
          </InfoCard>

          <InfoCard icon={Search} label="Trigger Condition">
            <p className="text-sm text-zinc-700 leading-relaxed">{task.condition_description}</p>
          </InfoCard>

          <InfoCard icon={Bell} label="When to Notify">
            <p className="text-sm font-mono uppercase tracking-wider text-zinc-700">
              {task.notify_behavior === 'once' && 'Once only'}
              {task.notify_behavior === 'always' && 'Every time'}
              {task.notify_behavior === 'track_state' && 'On changes'}
            </p>
            <div className="flex items-center gap-2 mt-3">
              <Switch
                checked={task.is_active}
                onCheckedChange={handleToggle}
                className="data-[state=checked]:bg-zinc-900 data-[state=unchecked]:bg-zinc-200 border-2 border-zinc-900"
              />
              <span className={`text-xs font-mono uppercase tracking-wider ${task.is_active ? 'text-zinc-700' : 'text-zinc-900 font-bold'}`}>
                {task.is_active ? "Active" : "Paused"}
              </span>
            </div>
          </InfoCard>

          <InfoCard icon={Mail} label="Notification Channels">
            {task.notification_channels && task.notification_channels.length > 0 ? (
              <div className="space-y-3">
                <NotificationChannelBadges
                  channels={task.notification_channels}
                  notificationEmail={task.notification_email}
                  webhookUrl={task.webhook_url}
                />
                <div className="space-y-1 text-xs font-mono text-zinc-600">
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
              <p className="text-sm font-mono text-zinc-600">No channels configured</p>
            )}
          </InfoCard>
        </div>
      </CollapsibleSection>

      {/* Notification Behavior Explanation - Miller's Law: Keep info concise (3-5 bullets) */}
      <div className="bg-muted/30 p-4 rounded-lg border border-border/50">
        <div className="flex items-start gap-3">
          <Bell className="h-5 w-5 text-muted-foreground mt-0.5 shrink-0" />
          <div className="flex-1">
            <h3 className="text-sm font-medium mb-1">How You'll Be Notified</h3>
            {task.notify_behavior === 'once' && (
              <p className="text-sm text-muted-foreground">
                <strong>Notify Once:</strong> You'll receive an email the first time we detect your condition is met,
                then monitoring will automatically stop. Perfect for one-time announcements like release dates.
              </p>
            )}
            {task.notify_behavior === 'always' && (
              <p className="text-sm text-muted-foreground">
                <strong>Always Notify:</strong> You'll receive an email every time your condition is met.
                Great for recurring opportunities like stock availability or price changes.
              </p>
            )}
            {task.notify_behavior === 'track_state' && (
              <p className="text-sm text-muted-foreground">
                <strong>Track Changes:</strong> You'll receive an email only when the information changes from our last check.
                Ideal for monitoring updates and changes over time.
              </p>
            )}
          </div>
        </div>
      </div>

      {task.last_known_state && (
        <CollapsibleSection
          title="Last Known State (Dev)"
          open={lastKnownStateExpanded}
          onOpenChange={setLastKnownStateExpanded}
          variant="dark"
        >
          <div className="bg-zinc-900 border-t-0 border border-zinc-800 p-4">
            <div className="text-xs font-mono space-y-2 overflow-x-auto">
              {Object.entries(task.last_known_state).map(([key, value]) => (
                <div key={key} className="flex flex-col gap-1">
                  <span className="text-zinc-400">{key.replace(/_/g, ' ')}</span>
                  {Array.isArray(value) ? (
                    value.length > 3 ? (
                      <span className="text-zinc-300 break-words">{value.slice(0, 3).join(", ")} +{value.length - 3} more</span>
                    ) : (
                      <span className="text-zinc-300 break-words">{value.join(", ")}</span>
                    )
                  ) : typeof value === "object" && value !== null ? (
                    <pre className="text-xs p-2 bg-zinc-950 text-zinc-400 border border-zinc-800 overflow-x-auto">
                      {JSON.stringify(value, null, 2)}
                    </pre>
                  ) : (
                    <span className="text-zinc-300 break-words">{String(value)}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </CollapsibleSection>
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
