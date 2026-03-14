import React, { useState, useEffect } from 'react';
import { AnimatePresence } from '@/lib/motion-compat';
import api from '@/lib/api';
import type { Task, FeedExecution } from '@/types';
import { TaskCard } from '@/components/TaskCard';
import { TaskListRow } from '@/components/TaskListRow';
import { TaskCreationDialog } from '@/components/TaskCreationDialog';
import { TaskPreviewModal } from '@/components/TaskPreviewModal';
import { TaskEditDialog } from '@/components/TaskEditDialog';
import { TaskDetailOverlay } from '@/components/TaskDetailOverlay';
import { ResultCard } from '@/components/ResultCard';
import { StatCard } from '@/components/ui/StatCard';
import {
  FilterGroup,
  EmptyState,
  SectionLabel,
} from '@/components/torale';
import { Plus, Search, Loader2, Filter, LayoutGrid, List as ListIcon, Inbox } from 'lucide-react';
import { toast } from 'sonner';
import { getTaskStatus, TaskActivityState } from '@/lib/taskStatus';
import { useAuth } from '@/contexts/AuthContext';
import { FirstTimeExperience } from '@/components/FirstTimeExperience';
import { useWelcomeFlow } from '@/hooks/useWelcomeFlow';
import { captureEvent } from '@/lib/posthog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

/**
 * Dashboard - Mission Control layout from MockDashboard.tsx
 * Grid-based task management with stats and filters
 */

interface DashboardProps {
  onTaskClick: (taskId: string, justCreated?: boolean) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onTaskClick }) => {
  const { user, isLoaded } = useAuth();
  const { handleWelcomeComplete } = useWelcomeFlow();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [feed, setFeed] = useState<FeedExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFeedLoading, setIsFeedLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('feed');
  const [isCreating, setIsCreating] = useState(false);
  const [previewTask, setPreviewTask] = useState<Task | null>(null);
  const [editTask, setEditTask] = useState<Task | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'completed' | 'paused'>('all');
  // Default to list on mobile (< 768px), grid on desktop
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(() =>
    typeof window !== 'undefined' && window.innerWidth < 768 ? 'list' : 'grid'
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [showWelcome, setShowWelcome] = useState(false);

  const handleFilterClick = (filter: 'all' | 'active' | 'completed' | 'paused') => {
    setActiveFilter(filter);
    captureEvent('filter_changed', { filter });
  };

  const loadTasks = async () => {
    setIsLoading(true);
    try {
      const data = await api.getTasks();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
      toast.error('Failed to load tasks');
    } finally {
      setIsLoading(false);
    }
  };

  const loadFeed = async () => {
    setIsFeedLoading(true);
    try {
      const data = await api.getFeed();
      setFeed(data);
    } catch (error) {
      console.error('Failed to load feed:', error);
    } finally {
      setIsFeedLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
    loadFeed();
  }, []); // Only load on mount

  useEffect(() => {
    if (isLoaded && user && !user.has_seen_welcome) {
      setShowWelcome(true);
    }
  }, [user, isLoaded]);

  const onWelcomeComplete = async () => {
    await handleWelcomeComplete();
    setShowWelcome(false);
  };

  const handleToggleTask = async (id: string, newState: 'active' | 'paused') => {
    try {
      await api.updateTask(id, { state: newState });
      await loadTasks();
      toast.success(newState === 'active' ? 'Task activated' : 'Task paused');

      captureEvent(newState === 'active' ? 'task_activated' : 'task_paused', {
        task_id: id,
      });
    } catch (error) {
      console.error('Failed to toggle task:', error);
      toast.error('Failed to update task');
    }
  };

  const handleDeleteTask = async (id: string) => {
    try {
      await api.deleteTask(id);
      await loadTasks();
      toast.success('Task deleted');

      captureEvent('task_deleted', {
        task_id: id,
      });
    } catch (error) {
      console.error('Failed to delete task:', error);
      toast.error('Failed to delete task');
    }
  };

  const handleExecuteTask = (id: string) => {
    const task = tasks.find((t) => t.id === id);
    if (task) {
      setPreviewTask(task);
    }
  };

  const handleEditTask = (id: string) => {
    const task = tasks.find((t) => t.id === id);
    if (task) {
      setEditTask(task);
    }
  };

  const handleTaskCreated = (task: Task) => {
    loadTasks();
    onTaskClick(task.id, true);

    captureEvent('task_created', {
      task_id: task.id,
    });
  };

  const handleTaskUpdated = (task: Task) => {
    // Update the task in local state immediately for instant UI feedback
    setTasks(prevTasks => prevTasks.map(t => t.id === task.id ? task : t));
  };

  // Filter and search tasks
  const filteredTasks = tasks.filter((task) => {
    // Filter by status
    if (activeFilter !== 'all') {
      const status = getTaskStatus(task.state);
      if (activeFilter === 'active' && status.activityState !== TaskActivityState.ACTIVE) return false;
      if (activeFilter === 'completed' && status.activityState !== TaskActivityState.COMPLETED) return false;
      if (activeFilter === 'paused' && status.activityState !== TaskActivityState.PAUSED) return false;
    }
    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        task.name.toLowerCase().includes(query) ||
        task.search_query.toLowerCase().includes(query)
      );
    }
    return true;
  });

  // Calculate stats
  const activeCount = tasks.filter((t) => t.state === 'active').length;
  const completedCount = tasks.filter((t) => t.state === 'completed').length;
  const pausedCount = tasks.filter((t) => t.state === 'paused').length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50">
      <main className="p-4 md:p-8 max-w-7xl mx-auto">
        {/* Header Area */}
        <header className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
            <div>
              <div className="flex items-center gap-2 text-zinc-400 text-[10px] font-mono uppercase tracking-wider mb-1">
                <span>Intelligence</span>
                <span>/</span>
                <span className="text-zinc-900">Mission Control</span>
              </div>
              <h1 className="text-3xl font-bold font-grotesk tracking-tight">Dashboard</h1>
            </div>

            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center justify-center gap-2 bg-zinc-900 text-white px-4 py-2.5 rounded-sm text-sm font-bold hover:bg-[hsl(10,90%,55%)] transition-colors shadow-brutalist active:translate-y-[1px] whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              New Monitor
            </button>
          </div>
        </header>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-zinc-200 pb-2">
            <TabsList className="bg-transparent p-0 gap-6">
              <TabsTrigger 
                value="feed" 
                className="bg-transparent p-0 pb-2 rounded-none border-b-2 border-transparent data-[state=active]:border-zinc-900 data-[state=active]:bg-transparent shadow-none font-bold font-grotesk"
              >
                My Feed
              </TabsTrigger>
              <TabsTrigger 
                value="monitors"
                className="bg-transparent p-0 pb-2 rounded-none border-b-2 border-transparent data-[state=active]:border-zinc-900 data-[state=active]:bg-transparent shadow-none font-bold font-grotesk"
              >
                Manage Monitors
              </TabsTrigger>
            </TabsList>
            
            <div className="flex items-center gap-2">
               <div className="relative flex-1 md:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400" />
                <input
                  type="text"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-1.5 bg-white border border-zinc-200 rounded-sm text-xs focus:outline-none focus:border-zinc-400 shadow-sm"
                />
              </div>
              {activeTab === 'monitors' && (
                <div className="flex bg-white border border-zinc-200 rounded-sm p-0.5">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-1 rounded-sm transition-colors ${viewMode === 'grid' ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400'}`}
                  >
                    <LayoutGrid className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-1 rounded-sm transition-colors ${viewMode === 'list' ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400'}`}
                  >
                    <ListIcon className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          </div>

          <TabsContent value="feed" className="mt-0 focus-visible:outline-none">
            {isFeedLoading ? (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="h-8 w-8 animate-spin text-zinc-300" />
              </div>
            ) : feed.length === 0 ? (
              <EmptyState
                icon={Inbox}
                title="Your feed is empty"
                description="Once your monitors find interesting results, they will appear here."
                action={{
                  label: 'Deploy New Monitor',
                  onClick: () => setIsCreating(true),
                }}
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {feed.map((execution) => (
                  <ResultCard 
                    key={execution.id} 
                    execution={execution} 
                    onClick={() => setSelectedTaskId(execution.task_id)}
                  />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="monitors" className="mt-0 focus-visible:outline-none">
            {/* Stats Row - Small and subtle now */}
            <div className="flex flex-wrap gap-4 mb-6">
              <div className="text-[10px] font-mono bg-emerald-50 text-emerald-700 px-2 py-1 border border-emerald-100 uppercase tracking-wider">{activeCount} Active</div>
              <div className="text-[10px] font-mono bg-zinc-100 text-zinc-600 px-2 py-1 border border-zinc-200 uppercase tracking-wider">{tasks.length} Total</div>
              <div className="text-[10px] font-mono bg-zinc-100 text-zinc-600 px-2 py-1 border border-zinc-200 uppercase tracking-wider">{completedCount} Completed</div>
            </div>

            {/* Filters */}
            <div className="mb-6">
              <FilterGroup<'all' | 'active' | 'completed' | 'paused'>
                filters={[
                  { id: 'all', label: 'All', count: tasks.length, icon: Filter },
                  { id: 'active', label: 'Active', count: activeCount },
                  { id: 'completed', label: 'Completed', count: completedCount },
                  { id: 'paused', label: 'Paused', count: pausedCount },
                ]}
                active={activeFilter}
                onChange={handleFilterClick}
                responsive={true}
              />
            </div>

            {filteredTasks.length === 0 ? (
              <EmptyState
                icon={Plus}
                title={searchQuery ? 'No monitors match your search' : 'No monitors found'}
                action={{
                  label: 'Create Monitor',
                  onClick: () => setIsCreating(true),
                }}
              />
            ) : viewMode === 'list' ? (
              <div className="md:bg-white md:border-2 md:border-zinc-200">
                <table className="w-full table-fixed">
                  <thead className="hidden md:table-header-group border-b-2 border-zinc-200 bg-zinc-50">
                    <tr>
                      <th className="p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider text-left">Monitor</th>
                      <th className="p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider text-left">Status</th>
                      <th className="p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider text-left">Last Run</th>
                      <th className="p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider text-left">Next Check</th>
                    </tr>
                  </thead>
                  <tbody>
                    <AnimatePresence>
                      {filteredTasks.map((task) => (
                        <TaskListRow
                          key={task.id}
                          task={task}
                          onToggle={handleToggleTask}
                          onDelete={handleDeleteTask}
                          onExecute={handleExecuteTask}
                          onEdit={handleEditTask}
                          onClick={setSelectedTaskId}
                        />
                      ))}
                    </AnimatePresence>
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                <AnimatePresence>
                  {filteredTasks.map((task) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      onToggle={handleToggleTask}
                      onDelete={handleDeleteTask}
                      onExecute={handleExecuteTask}
                      onEdit={handleEditTask}
                      onClick={setSelectedTaskId}
                    />
                  ))}
                </AnimatePresence>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>

      {/* Task Detail Sheet/Drawer Overlay */}
      <TaskDetailOverlay
        taskId={selectedTaskId}
        open={!!selectedTaskId}
        onOpenChange={(open) => !open && setSelectedTaskId(null)}
        currentUserId={user?.id}
        onDeleted={loadTasks}
      />

      {/* Dialogs */}
      <TaskCreationDialog
        open={isCreating}
        onOpenChange={setIsCreating}
        onTaskCreated={handleTaskCreated}
      />

      {editTask && (
        <TaskEditDialog
          task={editTask}
          open={!!editTask}
          onOpenChange={(open) => !open && setEditTask(null)}
          onSuccess={handleTaskUpdated}
        />
      )}

      {/* First-time experience overlay */}
      {showWelcome && <FirstTimeExperience onComplete={onWelcomeComplete} />}
    </div>
  );
};
