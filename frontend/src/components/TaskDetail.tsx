import React, { useState, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import type { Task, TaskExecution } from '@/types'
import { getResultDisplayText } from '@/types'
import api from '@/lib/api'
import { toast } from 'sonner'
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatusBadge } from "@/components/torale";
import { ExecutionTimeline } from "@/components/ExecutionTimeline";
import { TaskConfiguration } from "@/components/task/TaskConfiguration";
import { getTaskStatus } from '@/lib/taskStatus';
import { formatTimeUntil } from '@/lib/utils';
import {
  ArrowLeft,
  Clock,
  Bell,
  Play,
  Loader2,
  Trash2,
  Mail,
  Check,
  X,
  Copy,
  Eye,
  Users,
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
  currentUserId?: string; // Current user's ID (if authenticated)
}

export const TaskDetail: React.FC<TaskDetailProps> = ({
  taskId,
  onBack,
  onDeleted,
  currentUserId,
}) => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const isJustCreated = searchParams.get('justCreated') === 'true';
  const tabFromUrl = searchParams.get('tab') as 'executions' | 'notifications' | null;

  const [task, setTask] = useState<Task | null>(null);
  const [executions, setExecutions] = useState<TaskExecution[]>([]);
  const [notifications, setNotifications] = useState<TaskExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);
  const [activeTab, setActiveTab] = useState<string>(tabFromUrl || "executions");
  const [configExpanded, setConfigExpanded] = useState(false);
  const [isForking, setIsForking] = useState(false);

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
    const newParams = new URLSearchParams(searchParams);
    if (activeTab === 'executions') {
      newParams.delete('tab');
    } else {
      newParams.set('tab', activeTab);
    }

    if (newParams.toString() !== searchParams.toString()) {
      setSearchParams(newParams, { replace: true });
    }
  }, [activeTab, searchParams, setSearchParams]);

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
      const newState = task.state === 'active' ? 'paused' : 'active';
      await api.updateTask(taskId, { state: newState });
      await loadData();
      toast.success(newState === 'active' ? 'Task activated' : 'Task paused');
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

  const handleFork = async () => {
    setIsForking(true);
    try {
      const forkedTask = await api.forkTask(taskId);
      toast.success('Task copied to your dashboard!');
      navigate(`/tasks/${forkedTask.id}?justCreated=true`);
    } catch (error) {
      console.error("Failed to fork task:", error);
      toast.error('Failed to copy task');
    } finally {
      setIsForking(false);
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
  const status = getTaskStatus(task.state);

  // Determine if current user is the owner
  const isOwner = task.user_id === currentUserId;

  const firstExecution = executions[0];
  const isFirstExecutionComplete = firstExecution?.status === 'success';

  const handleDismissBanner = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete('justCreated');
    setSearchParams(newParams);
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
                Checks run automatically
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
                  Automated checks — frequency determined by AI
                </p>
              </div>
              <div className="flex items-start gap-2">
                <Bell className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                <p className="text-sm text-muted-foreground">
                  {task.notify_behavior === 'once' && 'Email when condition is met, then monitoring stops'}
                  {task.notify_behavior === 'always' && 'Email every time condition is met'}
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
              <StatusBadge variant={status.activityState} />
            </div>
            <div className="flex items-center gap-3 text-zinc-500 text-sm">
              <span className="truncate">{task.search_query}</span>
              {task.next_run ? (
                <span className="flex items-center gap-1 text-xs font-mono text-zinc-400 whitespace-nowrap">
                  <Clock className="w-3 h-3" />
                  Next check {formatTimeUntil(task.next_run)}
                </span>
              ) : task.state === 'completed' ? (
                <span className="flex items-center gap-1 text-xs font-mono text-zinc-400 whitespace-nowrap">
                  <Clock className="w-3 h-3" />
                  Monitoring complete
                </span>
              ) : null}
            </div>
          </div>
        </div>

      </div>

      {/* Latest Execution - Prominent on Mobile */}
      {firstExecution && (
        <div
          className="bg-white border-2 border-zinc-200 p-4 hover:border-zinc-400 transition-colors cursor-pointer"
          onClick={() => setActiveTab('executions')}
        >
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex items-center gap-2">
              <StatusBadge variant={firstExecution.status} />
              <span className="text-sm font-mono text-zinc-500">
                Latest result
              </span>
            </div>
            <span className="text-xs font-mono text-zinc-400">
              {new Date(firstExecution.started_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
              })}
            </span>
          </div>
          {getResultDisplayText(firstExecution.result) && (
            <div className="text-sm text-zinc-700 leading-relaxed line-clamp-3 prose prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p className="mb-0 leading-relaxed text-zinc-700">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc pl-5 mb-0 space-y-0">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-5 mb-0 space-y-0">{children}</ol>,
                  li: ({ children }) => <li className="text-sm leading-relaxed text-zinc-700">{children}</li>,
                  strong: ({ children }) => <strong className="font-bold text-zinc-900">{children}</strong>,
                }}
              >
                {getResultDisplayText(firstExecution.result)}
              </ReactMarkdown>
            </div>
          )}
        </div>
      )}

      {/* Action Buttons - Different for owner vs public viewer */}
      <div className="flex items-center gap-2">
        {!isOwner ? (
          // Public viewer: Show fork button and stats
          <>
            <Button
              onClick={handleFork}
              disabled={isForking}
              size="sm"
              className="gap-2"
            >
              {isForking ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
              {isForking ? 'Copying...' : 'Make a Copy'}
            </Button>
            {task.is_public && (
              <div className="flex items-center gap-4 text-sm text-muted-foreground ml-4">
                <div className="flex items-center gap-1">
                  <Eye className="h-4 w-4" />
                  {task.view_count}
                </div>
                <div className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  {task.subscriber_count}
                </div>
              </div>
            )}
          </>
        ) : (
          // Owner: Show run and delete buttons
          <>
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
              Run Now
            </Button>

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
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
          </>
        )}
      </div>

      {/* Task Configuration - Collapsible on Mobile, Always Visible on Desktop */}
      <TaskConfiguration
        task={task}
        configExpanded={configExpanded}
        onConfigExpandedChange={setConfigExpanded}
        onToggle={handleToggle}
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="sticky top-0 z-10 bg-zinc-50 pb-2 -mx-8 px-8">
          <div className="relative">
            <TabsList className="w-full overflow-x-auto flex-nowrap scrollbar-hide">
              <TabsTrigger value="executions">
                All Executions <span className="text-xs text-zinc-500 ml-1.5">({executions.length})</span>
              </TabsTrigger>
              <TabsTrigger value="notifications">
                Notifications <span className="text-xs text-zinc-500 ml-1.5">({notifications.length})</span>
              </TabsTrigger>
            </TabsList>
            {/* Scroll hint gradient */}
            <div className="absolute top-0 right-0 h-full w-12 bg-gradient-to-l from-zinc-50 to-transparent pointer-events-none" />
          </div>
        </div>

        <TabsContent value="executions" className="mt-6">
          <ExecutionTimeline executions={executions} />
        </TabsContent>

        <TabsContent value="notifications" className="mt-6">
          <ExecutionTimeline
            executions={notifications}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};
