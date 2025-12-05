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
import {
  SectionLabel,
  FilterGroup,
  EmptyState,
  StatusBadge,
  BrutalistTable,
  BrutalistTableHeader,
  BrutalistTableBody,
  BrutalistTableRow,
  BrutalistTableHead,
  BrutalistTableCell,
  ActionMenu,
  type FilterOption,
  type Action
} from '@/components/torale';
import { Plus, Search, Loader2, Filter, LayoutGrid, List as ListIcon, Play, Settings, Activity, CheckCircle, Pause, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { getTaskStatus, TaskActivityState } from '@/lib/taskStatus';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

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
  const [deleteTask, setDeleteTask] = useState<Task | null>(null);
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
      setDeleteTask(null);
      toast.success('Task deleted');
    } catch (error) {
      console.error('Failed to delete task:', error);
      toast.error('Failed to delete task');
    }
  };

  const confirmDelete = (task: Task) => {
    setDeleteTask(task);
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

        {/* Stats Row - Now clickable to filter */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          <div onClick={() => setActiveFilter('active')} className="cursor-pointer">
            <StatCard label="Active Monitors" value={activeCount.toString()} />
          </div>
          <div onClick={() => setActiveFilter('all')} className="cursor-pointer">
            <StatCard label="Total Tasks" value={tasks.length.toString()} />
          </div>
          <div onClick={() => setActiveFilter('completed')} className="cursor-pointer">
            <StatCard label="Completed" value={completedCount.toString()} />
          </div>
          <div onClick={() => setActiveFilter('paused')} className="cursor-pointer">
            <StatCard label="Paused" value={pausedCount.toString()} />
          </div>
        </div>

        {/* Filters & View Toggle */}
        <div className="flex justify-between items-center mb-6">
          <FilterGroup<'all' | 'active' | 'completed' | 'paused'>
            filters={[
              { id: 'all', label: 'All', count: tasks.length, icon: Filter },
              { id: 'active', label: 'Active', count: activeCount },
              { id: 'completed', label: 'Completed', count: completedCount },
              { id: 'paused', label: 'Paused', count: pausedCount },
            ]}
            active={activeFilter}
            onChange={setActiveFilter}
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
              className={`p-1.5 rounded-sm transition-colors ${viewMode === 'list' ? 'bg-zinc-100 text-zinc-900' : 'text-zinc-400 hover:text-zinc-600'}`}
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
          <BrutalistTable>
            <BrutalistTableHeader>
              <BrutalistTableRow>
                <BrutalistTableHead>Monitor</BrutalistTableHead>
                <BrutalistTableHead>Status</BrutalistTableHead>
                <BrutalistTableHead className="hidden md:table-cell">Schedule</BrutalistTableHead>
                <BrutalistTableHead className="hidden lg:table-cell">Last Run</BrutalistTableHead>
                <BrutalistTableHead align="right">Actions</BrutalistTableHead>
              </BrutalistTableRow>
            </BrutalistTableHeader>
            <BrutalistTableBody>
              <AnimatePresence>
                {filteredTasks.map((task) => {
                  const status = getTaskStatus(task.state);
                  const isTaskActive = task.state === 'active';

                  return (
                    <BrutalistTableRow
                      key={task.id}
                      onClick={() => onTaskClick(task.id)}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      <BrutalistTableCell>
                        <div className="flex flex-col gap-1">
                          <span className="font-grotesk font-bold text-sm">{task.name}</span>
                          <span className="text-xs text-zinc-500 truncate max-w-xs">{task.search_query}</span>
                        </div>
                      </BrutalistTableCell>
                      <BrutalistTableCell>
                        <StatusBadge variant={status.activityState} />
                      </BrutalistTableCell>
                      <BrutalistTableCell className="hidden md:table-cell">
                        <CronDisplay cron={task.schedule} className="text-sm font-mono text-zinc-600" showRaw={false} />
                      </BrutalistTableCell>
                      <BrutalistTableCell className="hidden lg:table-cell">
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
                      </BrutalistTableCell>
                      <BrutalistTableCell align="right">
                        <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => handleToggleTask(task.id, isTaskActive ? 'paused' : 'active')}
                            className="p-1.5 text-zinc-400 hover:text-zinc-900 hover:bg-zinc-100 rounded-sm transition-colors"
                            title={isTaskActive ? 'Pause monitor' : 'Resume monitor'}
                          >
                            {isTaskActive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                          </button>
                          <ActionMenu actions={[
                            { id: 'edit', label: 'Edit', icon: Settings, onClick: () => handleEditTask(task.id) },
                            { id: 'execute', label: 'Run Now', icon: Play, onClick: () => handleExecuteTask(task.id) },
                            { id: 'toggle', label: isTaskActive ? 'Pause' : 'Resume', icon: isTaskActive ? Pause : Play, onClick: () => handleToggleTask(task.id, isTaskActive ? 'paused' : 'active'), separator: true },
                            { id: 'delete', label: 'Delete', icon: Trash2, onClick: () => confirmDelete(task), variant: 'destructive' },
                          ]} />
                        </div>
                      </BrutalistTableCell>
                    </BrutalistTableRow>
                  );
                })}
              </AnimatePresence>
            </BrutalistTableBody>
          </BrutalistTable>
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

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteTask} onOpenChange={(open) => !open && setDeleteTask(null)}>
        <AlertDialogContent className="border-2 border-zinc-900 shadow-brutalist-lg">
          <AlertDialogHeader className="border-b-2 border-zinc-100 pb-4">
            <AlertDialogTitle className="font-grotesk">Delete Monitor</AlertDialogTitle>
            <AlertDialogDescription className="text-zinc-500">
              Are you sure you want to delete "{deleteTask?.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-3">
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => deleteTask && handleDeleteTask(deleteTask.id)} className="shadow-brutalist">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
