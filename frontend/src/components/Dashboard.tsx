import React, { useState, useEffect } from 'react';
import { AnimatePresence } from '@/lib/motion-compat';
import api from '@/lib/api';
import type { Task } from '@/types';
import { TaskCard } from '@/components/TaskCard';
import { TaskListRow } from '@/components/TaskListRow';
import { TaskCreationDialog } from '@/components/TaskCreationDialog';
import { TaskPreviewModal } from '@/components/TaskPreviewModal';
import { TaskEditDialog } from '@/components/TaskEditDialog';
import { StatCard } from '@/components/ui/StatCard';
import {
  FilterGroup,
  EmptyState,
} from '@/components/torale';
import { Plus, Search, Loader2, Filter, LayoutGrid, List as ListIcon } from 'lucide-react';
import { toast } from 'sonner';
import { getTaskStatus, TaskActivityState } from '@/lib/taskStatus';
import { useAuth } from '@/contexts/AuthContext';
import { FirstTimeExperience } from '@/components/FirstTimeExperience';
import { useWelcomeFlow } from '@/hooks/useWelcomeFlow';

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
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [previewTask, setPreviewTask] = useState<Task | null>(null);
  const [editTask, setEditTask] = useState<Task | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'completed' | 'paused'>('all');
  // Default to list on mobile (< 768px), grid on desktop
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(() =>
    typeof window !== 'undefined' && window.innerWidth < 768 ? 'list' : 'grid'
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [showWelcome, setShowWelcome] = useState(false);

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

  useEffect(() => {
    loadTasks();
  }, []); // Only load on mount - user sync now happens automatically in auth provider

  useEffect(() => {
    if (isLoaded && !user?.publicMetadata?.has_seen_welcome) {
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
      <main className="p-8">
        {/* Header Area */}
        <header className="mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
            <div>
              <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono mb-2">
                <span>Organization</span>
                <span>/</span>
                <span className="text-zinc-900">Monitors</span>
              </div>
              <h1 className="text-3xl font-bold font-grotesk tracking-tight">Mission Control</h1>
            </div>

            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center justify-center gap-2 bg-zinc-900 text-white px-4 py-2 rounded-sm text-sm font-bold hover:bg-[hsl(10,90%,55%)] transition-colors shadow-md active:translate-y-[1px] whitespace-nowrap"
            >
              <Plus className="w-4 h-4" />
              New Monitor
            </button>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
            <input
              type="text"
              placeholder="Search monitors..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-white border border-zinc-200 rounded-sm text-sm focus:outline-none focus:border-zinc-400 shadow-sm"
            />
          </div>
        </header>

        {/* Stats Row - Now clickable to filter */}
        <div className="hidden md:grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <button onClick={() => setActiveFilter('active')} className="text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 rounded-sm">
            <StatCard label="Active Monitors" value={activeCount.toString()} />
          </button>
          <button onClick={() => setActiveFilter('all')} className="text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 rounded-sm">
            <StatCard label="Total Tasks" value={tasks.length.toString()} />
          </button>
          <button onClick={() => setActiveFilter('completed')} className="text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 rounded-sm">
            <StatCard label="Completed" value={completedCount.toString()} />
          </button>
          <button onClick={() => setActiveFilter('paused')} className="text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-zinc-400 focus-visible:ring-offset-2 rounded-sm">
            <StatCard label="Paused" value={pausedCount.toString()} />
          </button>
        </div>

        {/* Filters & View Toggle */}
        <div className="flex justify-between items-center mb-6 gap-3">
          <FilterGroup<'all' | 'active' | 'completed' | 'paused'>
            filters={[
              { id: 'all', label: 'All', count: tasks.length, icon: Filter },
              { id: 'active', label: 'Active', count: activeCount },
              { id: 'completed', label: 'Completed', count: completedCount },
              { id: 'paused', label: 'Paused', count: pausedCount },
            ]}
            active={activeFilter}
            onChange={setActiveFilter}
            responsive={true}
          />

          <div className="flex bg-white border border-zinc-200 rounded-sm p-0.5">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-sm transition-colors ${viewMode === 'grid' ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400 hover:text-zinc-600'}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`inline-flex p-1.5 rounded-sm transition-colors ${viewMode === 'list' ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400 hover:text-zinc-600'}`}
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Monitors Grid/Table */}
        {filteredTasks.length === 0 ? (
          <EmptyState
            icon={Plus}
            title={searchQuery ? 'No monitors match your search' : 'Deploy New Monitor'}
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
                      onClick={onTaskClick}
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
                  onClick={onTaskClick}
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </main>

      {/* Dialogs */}
      <TaskCreationDialog
        open={isCreating}
        onOpenChange={setIsCreating}
        onTaskCreated={handleTaskCreated}
      />

      {previewTask && (
        <TaskPreviewModal
          task={previewTask}
          open={!!previewTask}
          onOpenChange={(open) => !open && setPreviewTask(null)}
          onEdit={handleEditTask}
          onViewHistory={onTaskClick}
        />
      )}

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
