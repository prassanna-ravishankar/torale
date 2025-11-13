import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import type { Task } from '@/types';
import { TaskCard } from '@/components/TaskCard';
import { TaskCreationWizard } from '@/components/TaskCreationWizard';
import { TaskPreviewModal } from '@/components/TaskPreviewModal';
import { TaskEditDialog } from '@/components/TaskEditDialog';
import { Button } from '@/components/ui/button';
import { Plus, Bell, RefreshCw, Loader2 } from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';

interface DashboardProps {
  onTaskClick: (taskId: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onTaskClick }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [previewTask, setPreviewTask] = useState<Task | null>(null);
  const [editTask, setEditTask] = useState<Task | null>(null);
  const [activeFilter, setActiveFilter] = useState<'all' | 'active' | 'triggered'>('all');
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
    // Sync user with backend on first load (creates user record if needed)
    // Only available in Clerk mode, no-op in no-auth mode
    if (syncUser) {
      syncUser().catch((error) => {
        console.error('Failed to sync user:', error);
        // Don't show error to user - sync will retry on next API call
      });
    }

    loadTasks();
  }, [syncUser]);

  const handleToggleTask = async (id: string, isActive: boolean) => {
    try {
      await api.updateTask(id, { is_active: isActive });
      await loadTasks();
      toast.success(isActive ? 'Task activated' : 'Task paused');
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
    toast.success('Task created! First execution started...');
  };

  const handleTaskUpdated = (task: Task) => {
    loadTasks();
  };

  const filteredTasks = tasks.filter((task) => {
    if (activeFilter === 'active') return task.is_active;
    if (activeFilter === 'triggered') return task.condition_met;
    return true;
  });

  const triggeredCount = tasks.filter((t) => t.condition_met).length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="mb-2">Monitoring Tasks</h1>
          <p className="text-muted-foreground">
            Manage your AI-powered web monitoring tasks
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" onClick={loadTasks}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button onClick={() => setIsCreating(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Task
          </Button>
        </div>
      </div>

      {triggeredCount > 0 && (
        <Alert>
          <Bell className="h-4 w-4" />
          <div className="ml-2">
            <p>
              You have {triggeredCount} task{triggeredCount > 1 ? 's' : ''} with triggered
              conditions.
            </p>
          </div>
        </Alert>
      )}

      <Tabs
        value={activeFilter}
        onValueChange={(v) => setActiveFilter(v as 'all' | 'active' | 'triggered')}
      >
        <TabsList>
          <TabsTrigger value="all">All Tasks ({tasks.length})</TabsTrigger>
          <TabsTrigger value="active">
            Active ({tasks.filter((t) => t.is_active).length})
          </TabsTrigger>
          <TabsTrigger value="triggered">Triggered ({triggeredCount})</TabsTrigger>
        </TabsList>

        <TabsContent value={activeFilter} className="mt-6">
          {filteredTasks.length === 0 ? (
            <div className="text-center py-12">
              <div className="mb-4">
                <Bell className="h-12 w-12 mx-auto text-muted-foreground" />
              </div>
              <h3 className="mb-2">
                {activeFilter === 'all' && 'No monitoring tasks yet'}
                {activeFilter === 'active' && 'No active tasks'}
                {activeFilter === 'triggered' && 'No triggered conditions'}
              </h3>
              <p className="text-muted-foreground mb-6">
                {activeFilter === 'all' && 'Create your first task to start monitoring the web'}
                {activeFilter === 'active' && 'Activate a task to start monitoring'}
                {activeFilter === 'triggered' && 'No tasks have met their trigger conditions yet'}
              </p>
              {activeFilter === 'all' && (
                <Button onClick={() => setIsCreating(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Your First Task
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Task Creation Wizard */}
      <TaskCreationWizard
        open={isCreating}
        onOpenChange={setIsCreating}
        onSuccess={handleTaskCreated}
      />

      {/* Task Preview Modal (Run Now) */}
      {previewTask && (
        <TaskPreviewModal
          open={!!previewTask}
          onOpenChange={(open) => !open && setPreviewTask(null)}
          task={previewTask}
          onEdit={handleEditTask}
          onViewHistory={onTaskClick}
        />
      )}

      {/* Task Edit Dialog */}
      {editTask && (
        <TaskEditDialog
          open={!!editTask}
          onOpenChange={(open) => !open && setEditTask(null)}
          task={editTask}
          onSuccess={handleTaskUpdated}
        />
      )}
    </div>
  );
};
