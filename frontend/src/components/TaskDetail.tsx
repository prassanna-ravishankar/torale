import React, { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import type { Task, TaskExecution } from '@/types'
import api from '@/lib/api'
import { toast } from 'sonner'
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatusBadge, DeleteMonitorDialog } from "@/components/torale";
import { ExecutionTimeline } from "@/components/ExecutionTimeline";
import { TaskConfiguration } from "@/components/task/TaskConfiguration";
import { ConnectorDegradationBanner } from "@/components/connectors/ConnectorDegradationBanner";
import { getTaskStatus } from '@/lib/taskStatus';
import { formatTimeUntil } from '@/lib/utils';
import {
  ArrowLeft,
  Clock,
  Play,
  Loader2,
  Trash2,
  Mail,
  Copy,
  ExternalLink,
  Settings,
  Activity,
} from "lucide-react";

interface TaskDetailProps {
  taskId: string;
  onBack: () => void;
  onDeleted: () => void;
  currentUserId?: string; // Current user's ID (if authenticated)
  compact?: boolean; // Whether to show a condensed view for drawers/feeds
}

export const TaskDetail: React.FC<TaskDetailProps> = ({
  taskId,
  onBack,
  onDeleted,
  currentUserId,
  compact = false,
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
  const [isForking, setIsForking] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

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

  const rssUrl = api.getTaskRssUrl(taskId);

  return (
    <div className={`mx-auto ${compact ? 'px-4 pb-8' : 'p-8 max-w-6xl space-y-6'}`}>
      {task.is_public && (
        <Helmet>
          <link
            rel="alternate"
            type="application/rss+xml"
            title={`${task.name} - RSS Feed`}
            href={rssUrl}
          />
        </Helmet>
      )}
      {/* Breadcrumb - Hidden in compact mode */}
      {!compact && (
        <div className="font-mono text-xs text-zinc-400 mb-4">
          <a href={task.is_public ? "/explore" : "/dashboard"} className="hover:text-zinc-900 transition-colors">
            {task.is_public ? "Explore" : "Monitors"}
          </a>
          {' / '}
          <span className="text-zinc-900">{task.name}</span>
        </div>
      )}

      {/* Header Section */}
      <div className={`flex flex-col ${compact ? 'gap-2 mb-4' : 'gap-4 mb-6'}`}>
        <div className="flex items-center gap-4">
          {!compact && (
            <Link to={task.is_public ? "/explore" : "/dashboard"}>
              <Button variant="ghost" size="icon" className="shrink-0">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h1 className={`font-grotesk font-bold truncate ${compact ? 'text-xl' : 'text-2xl md:text-4xl'}`}>
                {task.name}
              </h1>
              <StatusBadge variant={status.activityState} />
            </div>
            <div className="flex items-center gap-3 text-zinc-500 text-xs">
              <span className="truncate max-w-[200px]">{task.search_query}</span>
              {task.next_run && (
                <span className="flex items-center gap-1 text-[10px] font-mono text-zinc-400 whitespace-nowrap">
                  <Clock className="w-3 h-3" />
                  Next check {formatTimeUntil(task.next_run)}
                </span>
              )}
            </div>
          </div>
          
          {/* Header Actions */}
          <div className="flex items-center gap-1">
             {compact && (
                <Link to={`/tasks/${taskId}`}>
                  <Button
                    size="icon"
                    variant="ghost"
                    title="Open full page"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </Link>
             )}
             {!isOwner && (
                <Button
                  onClick={handleFork}
                  disabled={isForking}
                  size={compact ? "icon" : "sm"}
                  variant={compact ? "ghost" : "default"}
                  title="Copy to dashboard"
                  className={!compact ? "gap-2" : ""}
                >
                  {isForking ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                  {!compact && (isForking ? 'Copying...' : 'Make a Copy')}
                </Button>
             )}
             {isOwner && (
               <Button variant="ghost" size="icon" onClick={() => setShowDeleteDialog(true)}>
                 <Trash2 className="h-4 w-4" />
               </Button>
             )}
          </div>
        </div>
      </div>

      {isOwner && (
        <ConnectorDegradationBanner attachedSlugs={task.attached_connector_slugs ?? []} />
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="sticky top-0 z-10 bg-zinc-50 pb-2 -mx-4 px-4 sm:-mx-8 sm:px-8 border-b border-zinc-200 mb-6">
          <div className="relative">
            <TabsList className="bg-transparent p-0 gap-8 h-auto w-full justify-start rounded-none">
              <TabsTrigger 
                value="executions"
                className="px-0 pb-3 rounded-none border-b-2 border-transparent data-[state=active]:border-zinc-900 data-[state=active]:bg-transparent shadow-none font-bold font-grotesk flex items-center gap-2"
              >
                <Activity className="h-4 w-4" />
                Intelligence <span className="text-xs text-zinc-400 font-mono ml-1">({executions.length})</span>
              </TabsTrigger>
              <TabsTrigger 
                value="notifications"
                className="px-0 pb-3 rounded-none border-b-2 border-transparent data-[state=active]:border-zinc-900 data-[state=active]:bg-transparent shadow-none font-bold font-grotesk flex items-center gap-2"
              >
                <Mail className="h-4 w-4" />
                Findings <span className="text-xs text-zinc-400 font-mono ml-1">({notifications.length})</span>
              </TabsTrigger>
              <TabsTrigger 
                value="settings"
                className="px-0 pb-3 rounded-none border-b-2 border-transparent data-[state=active]:border-zinc-900 data-[state=active]:bg-transparent shadow-none font-bold font-grotesk flex items-center gap-2"
              >
                <Settings className="h-4 w-4" />
                Config
              </TabsTrigger>
            </TabsList>
          </div>
        </div>

        <TabsContent value="executions" className="mt-0 outline-none">
          <ExecutionTimeline executions={executions} isOwner={isOwner} />
        </TabsContent>

        <TabsContent value="notifications" className="mt-0 outline-none">
          <ExecutionTimeline
            executions={notifications}
            isOwner={isOwner}
          />
        </TabsContent>

        <TabsContent value="settings" className="mt-0 outline-none space-y-8">
          {isOwner && (
            <div className="flex flex-wrap items-center gap-3 p-6 bg-white border-2 border-zinc-200">
              <div className="flex-1 min-w-[200px]">
                <h4 className="font-bold text-sm mb-1">Quick Actions</h4>
                <p className="text-xs text-zinc-500 font-mono">Trigger manual runs or manage task lifecycle.</p>
              </div>
              <div className="flex items-center gap-2">
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
                <Button variant="outline" size="sm" onClick={() => setShowDeleteDialog(true)} className="text-red-600 hover:text-red-700 hover:bg-red-50 border-red-100">
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete Monitor
                </Button>
              </div>
            </div>
          )}

          <TaskConfiguration
            task={task}
            onToggle={handleToggle}
          />
          
          <DeleteMonitorDialog
            taskName={task.name}
            open={showDeleteDialog}
            onOpenChange={setShowDeleteDialog}
            onConfirm={handleDelete}
            extraDescription="All execution history will be permanently deleted."
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};
