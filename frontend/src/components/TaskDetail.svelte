<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { api } from '@/lib/apiClient';
  import type { Task, TaskExecution } from '@/lib/types';

  import Button from './ui/button.svelte';
  import Badge from './ui/badge.svelte';
  import Switch from './ui/switch.svelte';
  import Card from './ui/card.svelte';
  import Loader from './Loader.svelte';
  import ExecutionTimeline from './ExecutionTimeline.svelte';
  import StateComparison from './StateComparison.svelte';
  import { ArrowLeft, Clock, Search, Bell, Play, Loader2 as LoaderIcon, Trash2 } from 'lucide-svelte';

  export let taskId: string;
  export let onBack: () => void;
  export let onDeleted: () => void;


  let task: Task | null = null;
  let executions: TaskExecution[] = [];
  let notifications: TaskExecution[] = [];
  let isLoading = true;
  let isExecuting = false;
  let activeTab = 'executions';
  let showDeleteDialog = false;

  async function loadData() {
    isLoading = true;
    try {
      const [taskData, executionsData, notificationsData] = await Promise.all([
        api.getTask(taskId),
        api.getTaskExecutions(taskId),
        api.getTaskNotifications(taskId),
      ]);
      task = taskData;
      executions = executionsData;
      notifications = notificationsData;
    } catch (error) {
      console.error('Failed to load task details:', error);
      toast.error('Failed to load task details');
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadData();
  });

  async function handleToggle() {
    if (!task) return;
    try {
      await api.updateTask(taskId, { is_active: !task.is_active });
      await loadData();
      toast.success(task.is_active ? 'Task paused' : 'Task activated');
    } catch (error) {
      console.error('Failed to toggle task:', error);
      toast.error('Failed to update task');
    }
  }

  async function handleExecute() {
    isExecuting = true;
    try {
      await api.executeTask(taskId);
      toast.success('Task execution started');
      await loadData();
    } catch (error) {
      console.error('Failed to execute task:', error);
      toast.error('Failed to execute task');
    } finally {
      isExecuting = false;
    }
  }

  async function handleDelete() {
    try {
      await api.deleteTask(taskId);
      toast.success('Task deleted');
      onDeleted();
    } catch (error) {
      console.error('Failed to delete task:', error);
      toast.error('Failed to delete task');
    }
  }
</script>

{#if isLoading}
  <div class="flex items-center justify-center min-h-[400px]">
    <Loader />
  </div>
{:else if !task}
  <div class="text-center py-12">
    <p class="text-muted-foreground mb-4">Task not found</p>
    <Button on:click={onBack}>
      <ArrowLeft class="mr-2 h-4 w-4" />
      Back to Dashboard
    </Button>
  </div>
{:else}
  <div class="space-y-6">
    <div class="flex items-start justify-between">
      <div class="flex items-start gap-4 flex-1">
        <Button variant="ghost" size="icon" on:click={onBack}>
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-2">
            <h1 class="text-3xl font-bold">{task.name}</h1>
            {#if task.condition_met}
              <Badge variant="default">Triggered</Badge>
            {/if}
            {#if !task.is_active}
              <Badge variant="secondary">Paused</Badge>
            {/if}
          </div>
          <p class="text-muted-foreground">{task.search_query}</p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="outline" on:click={handleExecute} disabled={isExecuting}>
          {#if isExecuting}
            <LoaderIcon class="mr-2 h-4 w-4 animate-spin" />
          {:else}
            <Play class="mr-2 h-4 w-4" />
          {/if}
          Run Now
        </Button>

        <Button variant="outline" size="icon" on:click={() => (showDeleteDialog = true)}>
          <Trash2 class="h-4 w-4" />
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card class="p-4">
        <div class="flex items-center gap-2 text-muted-foreground mb-3">
          <Clock class="h-4 w-4" />
          <p class="text-sm">Schedule</p>
        </div>
        <p class="font-mono text-sm">{task.schedule}</p>
      </Card>

      <Card class="p-4">
        <div class="flex items-center gap-2 text-muted-foreground mb-3">
          <Search class="h-4 w-4" />
          <p class="text-sm">Trigger Condition</p>
        </div>
        <p class="text-sm">{task.condition_description}</p>
      </Card>

      <Card class="p-4">
        <div class="flex items-center gap-2 text-muted-foreground mb-3">
          <Bell class="h-4 w-4" />
          <p class="text-sm">Notification Behavior</p>
        </div>
        <p class="capitalize mb-3 text-sm">{task.notify_behavior.replace('_', ' ')}</p>
        <div class="flex items-center gap-2">
          <Switch checked={task.is_active} on:click={handleToggle} />
          <span class="text-sm text-muted-foreground">
            {task.is_active ? 'Active' : 'Paused'}
          </span>
        </div>
      </Card>
    </div>

    {#if task.last_known_state}
      <Card class="p-4">
        <h3 class="text-lg font-semibold mb-4">Last Known State</h3>
        <div class="text-sm space-y-2">
          {#each Object.entries(task.last_known_state) as [key, value]}
            <div class="flex items-start gap-2">
              <span class="font-medium min-w-[150px]">{key}:</span>
              <span class="text-muted-foreground">
                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
              </span>
            </div>
          {/each}
        </div>
      </Card>
    {/if}

    <div class="space-y-4">
      <div class="flex gap-2 border-b">
        <button
          class="px-4 py-2 text-sm font-medium {activeTab === 'executions' ? 'border-b-2 border-primary' : 'text-muted-foreground'}"
          on:click={() => (activeTab = 'executions')}
        >
          All Executions ({executions.length})
        </button>
        <button
          class="px-4 py-2 text-sm font-medium {activeTab === 'notifications' ? 'border-b-2 border-primary' : 'text-muted-foreground'}"
          on:click={() => (activeTab = 'notifications')}
        >
          Notifications ({notifications.length})
        </button>
        <button
          class="px-4 py-2 text-sm font-medium {activeTab === 'changes' ? 'border-b-2 border-primary' : 'text-muted-foreground'}"
          on:click={() => (activeTab = 'changes')}
        >
          State Changes
        </button>
      </div>

      {#if activeTab === 'executions'}
        <ExecutionTimeline {executions} />
      {:else if activeTab === 'notifications'}
        <ExecutionTimeline executions={notifications} highlightNotifications={true} />
      {:else}
        <StateComparison {executions} />
      {/if}
    </div>
  </div>

  {#if showDeleteDialog}
    <div
      class="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
      on:click={() => (showDeleteDialog = false)}
      on:keydown={(e) => e.key === 'Escape' && (showDeleteDialog = false)}
      role="button"
      tabindex="0"
    >
      <div class="fixed left-[50%] top-[50%] z-50 translate-x-[-50%] translate-y-[-50%] w-full max-w-lg">
        <div class="bg-background p-6 shadow-lg rounded-lg border space-y-4">
          <div>
            <h3 class="text-lg font-semibold">Delete Task</h3>
            <p class="text-sm text-muted-foreground mt-2">
              Are you sure you want to delete "{task.name}"? This action cannot be undone. All execution history will be permanently deleted.
            </p>
          </div>
          <div class="flex gap-2 justify-end">
            <Button variant="outline" on:click={() => (showDeleteDialog = false)}>Cancel</Button>
            <Button
              variant="destructive"
              on:click={() => {
                showDeleteDialog = false;
                handleDelete();
              }}
            >
              Delete
            </Button>
          </div>
        </div>
      </div>
    </div>
  {/if}
{/if}
