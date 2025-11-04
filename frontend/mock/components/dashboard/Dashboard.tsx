import React, { useState, useEffect } from "react";
import { Task } from "../../types";
import { tasksApi } from "../../lib/mockApi";
import { TaskCard } from "./TaskCard";
import { TaskCreationDialog } from "../tasks/TaskCreationDialog";
import { Button } from "../ui/button";
import { Plus, Bell, RefreshCw, Loader2 } from "lucide-react";
import { Alert } from "../ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";

interface DashboardProps {
  onTaskClick: (taskId: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onTaskClick }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [activeFilter, setActiveFilter] = useState<"all" | "active" | "triggered">(
    "all"
  );

  const loadTasks = async () => {
    setIsLoading(true);
    try {
      const data = await tasksApi.getTasks();
      setTasks(data);
    } catch (error) {
      console.error("Failed to load tasks:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const handleToggleTask = async (id: string, isActive: boolean) => {
    try {
      await tasksApi.updateTask(id, { is_active: isActive });
      await loadTasks();
    } catch (error) {
      console.error("Failed to toggle task:", error);
    }
  };

  const handleDeleteTask = async (id: string) => {
    try {
      await tasksApi.deleteTask(id);
      await loadTasks();
    } catch (error) {
      console.error("Failed to delete task:", error);
    }
  };

  const handleExecuteTask = async (id: string) => {
    try {
      await tasksApi.executeTask(id);
      await loadTasks();
    } catch (error) {
      console.error("Failed to execute task:", error);
    }
  };

  const filteredTasks = tasks.filter((task) => {
    if (activeFilter === "active") return task.is_active;
    if (activeFilter === "triggered") return task.condition_met;
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
              You have {triggeredCount} task{triggeredCount > 1 ? "s" : ""} with
              triggered conditions.
            </p>
          </div>
        </Alert>
      )}

      <Tabs value={activeFilter} onValueChange={(v) => setActiveFilter(v as any)}>
        <TabsList>
          <TabsTrigger value="all">All Tasks ({tasks.length})</TabsTrigger>
          <TabsTrigger value="active">
            Active ({tasks.filter((t) => t.is_active).length})
          </TabsTrigger>
          <TabsTrigger value="triggered">
            Triggered ({triggeredCount})
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeFilter} className="mt-6">
          {filteredTasks.length === 0 ? (
            <div className="text-center py-12">
              <div className="mb-4">
                <Bell className="h-12 w-12 mx-auto text-muted-foreground" />
              </div>
              <h3 className="mb-2">
                {activeFilter === "all" && "No monitoring tasks yet"}
                {activeFilter === "active" && "No active tasks"}
                {activeFilter === "triggered" && "No triggered conditions"}
              </h3>
              <p className="text-muted-foreground mb-6">
                {activeFilter === "all" &&
                  "Create your first task to start monitoring the web"}
                {activeFilter === "active" &&
                  "Activate a task to start monitoring"}
                {activeFilter === "triggered" &&
                  "No tasks have met their trigger conditions yet"}
              </p>
              {activeFilter === "all" && (
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
                  onClick={onTaskClick}
                />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      <TaskCreationDialog
        open={isCreating}
        onOpenChange={setIsCreating}
        onTaskCreated={loadTasks}
      />
    </div>
  );
};
