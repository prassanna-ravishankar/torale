<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { api } from '@/lib/apiClient';
  import type { Task } from '@/lib/types';

  import TaskCard from './TaskCard.svelte';
  import TaskCreationDialog from './TaskCreationDialog.svelte';
  import Button from './ui/Button.svelte';
  import Loader from './Loader.svelte';
  import { Plus, Bell, RefreshCw } from 'lucide-svelte';

  export let onTaskClick: (taskId: string) => void;


  let tasks: Task[] = [];
  let isLoading = true;
  let isCreating = false;
  let activeFilter: 'all' | 'active' | 'triggered' = 'all';


  async function loadTasks() {
    isLoading = true;
    try {
      const data = await api.getTasks();
      tasks = data;
    } catch (error) {
      console.error('Failed to load tasks:', error);
      toast.error('Failed to load tasks');
    } finally {
      isLoading = false;
    }
  }

  onMount(async () => {
    // Sync user with backend on first load
    try {
      await api.syncUser();
    } catch (error) {
      console.error('Failed to sync user:', error);
    }

    loadTasks();
  });

  async function handleToggleTask(id: string, isActive: boolean) {
    try {
      await api.updateTask(id, { is_active: isActive });
      await loadTasks();
      toast.success(isActive ? 'Task activated' : 'Task paused');
    } catch (error) {
      console.error('Failed to toggle task:', error);
      toast.error('Failed to update task');
    }
  }

  async function handleDeleteTask(id: string) {
    try {
      await api.deleteTask(id);
      await loadTasks();
      toast.success('Task deleted');
    } catch (error) {
      console.error('Failed to delete task:', error);
      toast.error('Failed to delete task');
    }
  }

  async function handleExecuteTask(id: string) {
    try {
      await api.executeTask(id);
      toast.success('Task execution started');
      await loadTasks();
    } catch (error) {
      console.error('Failed to execute task:', error);
      toast.error('Failed to execute task');
    }
  }

  $: filteredTasks = tasks.filter((task) => {
    if (activeFilter === 'active') return task.is_active;
    if (activeFilter === 'triggered') return task.condition_met;
    return true;
  });

  $: triggeredCount = tasks.filter((t) => t.condition_met).length;
</script>

{#if isLoading}
  <div class="flex items-center justify-center min-h-[400px]">
    <Loader />
  </div>
{:else}
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold mb-2">Monitoring Tasks</h1>
        <p class="text-muted-foreground">
          Manage your AI-powered web monitoring tasks
        </p>
      </div>
      <div class="flex items-center gap-3">
        <Button variant="outline" size="icon" on:click={loadTasks}>
          <RefreshCw class="h-4 w-4" />
        </Button>
        <Button on:click={() => (isCreating = true)}>
          <Plus class="mr-2 h-4 w-4" />
          New Task
        </Button>
      </div>
    </div>

    {#if triggeredCount > 0}
      <div class="flex items-center gap-2 p-4 rounded-lg border bg-card">
        <Bell class="h-4 w-4" />
        <p class="text-sm">
          You have {triggeredCount} task{triggeredCount > 1 ? 's' : ''} with triggered conditions.
        </p>
      </div>
    {/if}

    <div class="space-y-4">
      <div class="flex gap-2 border-b">
        <button
          class="px-4 py-2 text-sm font-medium {activeFilter === 'all' ? 'border-b-2 border-primary' : 'text-muted-foreground'}"
          on:click={() => (activeFilter = 'all')}
        >
          All Tasks ({tasks.length})
        </button>
        <button
          class="px-4 py-2 text-sm font-medium {activeFilter === 'active' ? 'border-b-2 border-primary' : 'text-muted-foreground'}"
          on:click={() => (activeFilter = 'active')}
        >
          Active ({tasks.filter((t) => t.is_active).length})
        </button>
        <button
          class="px-4 py-2 text-sm font-medium {activeFilter === 'triggered' ? 'border-b-2 border-primary' : 'text-muted-foreground'}"
          on:click={() => (activeFilter = 'triggered')}
        >
          Triggered ({triggeredCount})
        </button>
      </div>

      <div class="mt-6">
        {#if filteredTasks.length === 0}
          <div class="text-center py-12">
            <div class="mb-4">
              <Bell class="h-12 w-12 mx-auto text-muted-foreground" />
            </div>
            <h3 class="text-lg font-semibold mb-2">
              {#if activeFilter === 'all'}
                No monitoring tasks yet
              {:else if activeFilter === 'active'}
                No active tasks
              {:else}
                No triggered conditions
              {/if}
            </h3>
            <p class="text-muted-foreground mb-6">
              {#if activeFilter === 'all'}
                Create your first task to start monitoring the web
              {:else if activeFilter === 'active'}
                Activate a task to start monitoring
              {:else}
                No tasks have met their trigger conditions yet
              {/if}
            </p>
            {#if activeFilter === 'all'}
              <Button on:click={() => (isCreating = true)}>
                <Plus class="mr-2 h-4 w-4" />
                Create Your First Task
              </Button>
            {/if}
          </div>
        {:else}
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {#each filteredTasks as task (task.id)}
              <TaskCard
                {task}
                onToggle={handleToggleTask}
                onDelete={handleDeleteTask}
                onExecute={handleExecuteTask}
                onClick={onTaskClick}
              />
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <TaskCreationDialog
      open={isCreating}
      onOpenChange={(open) => (isCreating = open)}
      onTaskCreated={loadTasks}
    />
  </div>
{/if}
