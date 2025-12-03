import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from '@/lib/motion-compat';
import api from '@/lib/api';
import type { Task } from '@/types';
import { TaskCard } from '@/components/TaskCard';
import { TaskCreationDialog } from '@/components/TaskCreationDialog';
import { TaskPreviewModal } from '@/components/TaskPreviewModal';
import { TaskEditDialog } from '@/components/TaskEditDialog';
import { StatCard } from '@/components/ui/StatCard';
import { CronDisplay } from '@/components/ui/CronDisplay';
import { Button } from '@/components/ui/button';
import { Plus, Search, Loader2, Filter, LayoutGrid, List as ListIcon, Play, Settings, Activity, CheckCircle, Pause } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { getTaskStatus, TaskActivityState } from '@/lib/taskStatus';

/**
 * Dashboard - Mission Control layout from MockDashboard.tsx
 * Grid-based task management with stats and filters
 */

interface DashboardProps {
  onTaskClick: (taskId: string, justCreated?: boolean) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onTaskClick }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [previewTask, setPreviewTask] = useState<Task | null>(null);
  const [editTask, setEditTask] = useState<Task | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'completed' | 'paused'>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const { syncUser } = useAuth();

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
    if (syncUser) {
      syncUser().catch((error) => {
        console.error('Failed to sync user:', error);
      });
    }
    loadTasks();
  }, [syncUser]);

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
    loadTasks();
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

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <StatCard label="Active Monitors" value={activeCount.toString()} />
          <StatCard label="Total Tasks" value={tasks.length.toString()} />
          <StatCard label="Completed" value={completedCount.toString()} />
          <StatCard label="Paused" value={pausedCount.toString()} />
        </div>

        {/* Filters & View Toggle */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveFilter('all')}
              className={`px-3 py-1.5 border border-zinc-200 rounded-sm text-xs font-medium transition-colors flex items-center gap-2 ${
                activeFilter === 'all'
                  ? 'bg-zinc-900 text-white border-zinc-900'
                  : 'bg-white text-zinc-600 hover:border-zinc-400'
              }`}
            >
              <Filter className="w-3 h-3" />
              All ({tasks.length})
            </button>
            <button
              onClick={() => setActiveFilter('active')}
              className={`px-3 py-1.5 border border-zinc-200 rounded-sm text-xs font-medium transition-colors ${
                activeFilter === 'active'
                  ? 'bg-zinc-900 text-white border-zinc-900'
                  : 'bg-white text-zinc-600 hover:border-zinc-400'
              }`}
            >
              Active ({activeCount})
            </button>
            <button
              onClick={() => setActiveFilter('completed')}
              className={`px-3 py-1.5 border border-zinc-200 rounded-sm text-xs font-medium transition-colors ${
                activeFilter === 'completed'
                  ? 'bg-zinc-900 text-white border-zinc-900'
                  : 'bg-white text-zinc-600 hover:border-zinc-400'
              }`}
            >
              Completed ({completedCount})
            </button>
            <button
              onClick={() => setActiveFilter('paused')}
              className={`px-3 py-1.5 border border-zinc-200 rounded-sm text-xs font-medium transition-colors ${
                activeFilter === 'paused'
                  ? 'bg-zinc-900 text-white border-zinc-900'
                  : 'bg-white text-zinc-600 hover:border-zinc-400'
              }`}
            >
              Paused ({pausedCount})
            </button>
          </div>

          <div className="flex bg-white border border-zinc-200 rounded-sm p-0.5">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-sm transition-colors ${viewMode === 'grid' ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400 hover:text-zinc-600'}`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1.5 rounded-sm transition-colors ${viewMode === 'list' ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400 hover:text-zinc-600'}`}
            >
              <ListIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Monitors Grid/Table */}
        {filteredTasks.length === 0 ? (
          <motion.button
            onClick={() => setIsCreating(true)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="w-full border-2 border-dashed border-zinc-200 rounded-sm flex flex-col items-center justify-center p-12 text-zinc-400 hover:border-zinc-400 hover:text-zinc-600 transition-all group min-h-[200px]"
          >
            <div className="w-12 h-12 rounded-full bg-zinc-50 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Plus className="w-6 h-6" />
            </div>
            <span className="font-mono text-xs uppercase tracking-widest font-bold">
              {searchQuery ? 'No monitors match your search' : 'Deploy New Monitor'}
            </span>
          </motion.button>
        ) : viewMode === 'list' ? (
          <div className="bg-white border-2 border-zinc-200 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-zinc-200 bg-zinc-50">
                  <th className="text-left p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider">Monitor</th>
                  <th className="text-left p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider">Status</th>
                  <th className="text-left p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider hidden md:table-cell">Schedule</th>
                  <th className="text-left p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider hidden lg:table-cell">Last Run</th>
                  <th className="text-right p-4 text-[10px] font-mono uppercase text-zinc-400 tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {filteredTasks.map((task) => {
                    const status = getTaskStatus(task.state);
                    const StatusIcon = {
                      Activity,
                      CheckCircle,
                      Pause,
                    }[status.iconName];

                    return (
                      <motion.tr
                        key={task.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="border-b border-zinc-200 hover:bg-zinc-50 transition-colors cursor-pointer"
                        onClick={() => onTaskClick(task.id)}
                      >
                        <td className="p-4">
                          <div className="flex flex-col gap-1">
                            <span className="font-grotesk font-bold text-sm">{task.name}</span>
                            <span className="text-xs text-zinc-500 truncate max-w-xs">{task.search_query}</span>
                          </div>
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <StatusIcon className="h-4 w-4" style={{ color: status.color }} />
                            <span className="text-sm whitespace-nowrap">{status.label}</span>
                          </div>
                        </td>
                        <td className="p-4 hidden md:table-cell">
                          <CronDisplay cron={task.schedule} className="text-sm font-mono text-zinc-600" showRaw={false} />
                        </td>
                        <td className="p-4 hidden lg:table-cell">
                          {task.last_execution ? (
                            <span className="text-sm text-zinc-600">
                              {new Date(task.last_execution.started_at).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                hour: 'numeric',
                                minute: '2-digit',
                              })}
                            </span>
                          ) : (
                            <span className="text-sm text-zinc-400">Never</span>
                          )}
                        </td>
                        <td className="p-4">
                          <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleExecuteTask(task.id)}
                              className="h-8 w-8 p-0"
                            >
                              <Play className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditTask(task.id)}
                              className="h-8 w-8 p-0"
                            >
                              <Settings className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </motion.tr>
                    );
                  })}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
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
    </div>
  );
};
