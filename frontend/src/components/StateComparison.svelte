<script lang="ts">
  import type { TaskExecution } from '@/lib/types';
  import Card from './ui/card.svelte';
  import { ArrowRight, Info } from 'lucide-svelte';

  export let executions: TaskExecution[];

  $: changedExecutions = executions.filter((e) => e.change_summary || e.condition_met);

  function formatDate(dateStr: string) {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(date);
  }
</script>

{#if changedExecutions.length === 0}
  <div class="text-center py-12">
    <Info class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
    <h3 class="text-lg font-semibold mb-2">No state changes detected</h3>
    <p class="text-muted-foreground">
      When the monitored information changes, you'll see a comparison here.
    </p>
  </div>
{:else}
  <div class="space-y-4">
    <div class="flex items-center gap-2 p-4 rounded-lg border bg-card">
      <Info class="h-4 w-4 shrink-0" />
      <p class="text-sm">
        This view shows executions where the state changed or the trigger condition was met.
      </p>
    </div>

    {#each changedExecutions as execution, index (execution.id)}
      {@const nextExecution = changedExecutions[index + 1]}
      <Card class="p-4">
        <div class="mb-3">
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-lg font-semibold">{formatDate(execution.started_at)}</h3>
            {#if execution.condition_met}
              <span class="text-sm px-2 py-1 bg-primary text-primary-foreground rounded">
                Condition Met
              </span>
            {/if}
          </div>
          {#if execution.change_summary}
            <p class="text-sm text-muted-foreground">{execution.change_summary}</p>
          {/if}
        </div>

        {#if execution.result?.current_state}
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            {#if nextExecution?.result?.current_state}
              <div class="space-y-2">
                <p class="text-sm font-medium">Previous State:</p>
                <div class="p-3 bg-muted rounded-md">
                  <div class="text-xs text-muted-foreground space-y-1">
                    {#each Object.entries(nextExecution.result.current_state) as [key, value]}
                      <div>
                        <span class="font-medium">{key}:</span>
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </div>
                    {/each}
                  </div>
                </div>
              </div>
            {/if}

            <div class="space-y-2">
              <p class="text-sm font-medium">
                {nextExecution?.result?.current_state ? 'New State:' : 'Current State:'}
              </p>
              <div class="p-3 bg-primary/10 border border-primary/20 rounded-md">
                <div class="text-xs space-y-1">
                  {#each Object.entries(execution.result.current_state) as [key, value]}
                    {@const previousValue = nextExecution?.result?.current_state?.[key]}
                    {@const hasChanged =
                      previousValue !== undefined &&
                      JSON.stringify(previousValue) !== JSON.stringify(value)}
                    <div class={hasChanged ? 'font-medium text-primary' : ''}>
                      <span class="font-medium">{key}:</span>
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      {#if hasChanged}
                        <ArrowRight class="inline h-3 w-3 mx-1" />
                      {/if}
                    </div>
                  {/each}
                </div>
              </div>
            </div>
          </div>
        {/if}

        {#if execution.result?.answer}
          <div class="mt-3 p-3 bg-muted rounded-md">
            <p class="text-sm">{execution.result.answer}</p>
          </div>
        {/if}
      </Card>
    {/each}
  </div>
{/if}
