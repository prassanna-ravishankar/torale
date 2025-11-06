<script lang="ts">
  import type { Task } from '@/lib/types';
  import Card from './ui/card.svelte';
  import Badge from './ui/badge.svelte';
  import Button from './ui/button.svelte';
  import Switch from './ui/switch.svelte';
  import { Clock, Search, ExternalLink, MoreVertical, Trash2, Play } from 'lucide-svelte';

  export let task: Task;
  export let onToggle: (id: string, isActive: boolean) => void;
  export let onDelete: (id: string) => void;
  export let onExecute: (id: string) => void;
  export let onClick: (id: string) => void;

  let showMenu = false;

  function handleToggle(e: MouseEvent) {
    e.stopPropagation();
    onToggle(task.id, !task.is_active);
  }

  function handleDelete(e: MouseEvent) {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete "${task.name}"?`)) {
      onDelete(task.id);
    }
    showMenu = false;
  }

  function handleExecute(e: MouseEvent) {
    e.stopPropagation();
    onExecute(task.id);
    showMenu = false;
  }

  function handleCardClick() {
    onClick(task.id);
  }
</script>

<Card class="cursor-pointer hover:border-primary transition-colors">
  <div on:click={handleCardClick} on:keydown={(e) => e.key === 'Enter' && handleCardClick()} role="button" tabindex="0">
    <!-- Header -->
    <div class="p-4 pb-3">
      <div class="flex items-start justify-between">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-2">
            <h3 class="text-lg font-semibold truncate">{task.name}</h3>
            {#if task.condition_met}
              <Badge variant="default">Triggered</Badge>
            {/if}
            {#if !task.is_active}
              <Badge variant="secondary">Paused</Badge>
            {/if}
          </div>
          <p class="text-sm text-muted-foreground line-clamp-2">
            {task.search_query}
          </p>
        </div>

        <div class="relative ml-2">
          <Button
            variant="ghost"
            size="icon"
            on:click={(e) => {
              e.stopPropagation();
              showMenu = !showMenu;
            }}
          >
            <MoreVertical class="h-4 w-4" />
          </Button>

          {#if showMenu}
            <div class="absolute right-0 mt-2 w-48 rounded-md border bg-popover p-1 shadow-md z-10">
              <button
                class="w-full text-left px-2 py-1.5 text-sm rounded-sm hover:bg-accent flex items-center gap-2"
                on:click={handleExecute}
              >
                <Play class="h-4 w-4" />
                Run Now
              </button>
              <div class="h-px bg-border my-1" />
              <button
                class="w-full text-left px-2 py-1.5 text-sm rounded-sm hover:bg-accent text-destructive flex items-center gap-2"
                on:click={handleDelete}
              >
                <Trash2 class="h-4 w-4" />
                Delete Task
              </button>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="px-4 pb-3 space-y-3">
      <div class="flex items-center gap-2 text-sm text-muted-foreground">
        <Clock class="h-4 w-4 shrink-0" />
        <span class="font-mono text-xs">{task.schedule}</span>
      </div>

      <div class="flex items-start gap-2 text-sm text-muted-foreground">
        <Search class="h-4 w-4 shrink-0 mt-0.5" />
        <span class="line-clamp-2">{task.condition_description}</span>
      </div>

      {#if task.condition_met && task.last_known_state}
        <div class="p-2.5 bg-muted/50 rounded-md border border-muted">
          <p class="text-xs text-muted-foreground">
            📊 State captured - click "View Details" for full information
          </p>
        </div>
      {/if}
    </div>

    <!-- Footer -->
    <div class="flex items-center justify-between px-4 pt-3 pb-4 border-t">
      <div class="flex items-center gap-2" on:click={handleToggle} on:keydown={(e) => e.key === 'Enter' && handleToggle(e)} role="button" tabindex="0">
        <Switch checked={task.is_active} />
        <span class="text-sm text-muted-foreground">
          {task.is_active ? 'Active' : 'Paused'}
        </span>
      </div>

      <Button
        variant="ghost"
        size="sm"
        on:click={(e) => {
          e.stopPropagation();
          onClick(task.id);
        }}
      >
        View Details
        <ExternalLink class="ml-2 h-3 w-3" />
      </Button>
    </div>
  </div>
</Card>

<svelte:window on:click={() => (showMenu = false)} />
