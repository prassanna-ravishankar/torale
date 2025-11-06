<script lang="ts">
  import type { TaskExecution } from '@/lib/types';
  import Badge from './ui/badge.svelte';
  import Card from './ui/card.svelte';
  import { CheckCircle2, XCircle, Clock, ExternalLink, AlertCircle } from 'lucide-svelte';

  export let executions: TaskExecution[];
  export let highlightNotifications = false;

  function getStatusIcon(status: string) {
    switch (status) {
      case 'success':
        return CheckCircle2;
      case 'failed':
        return XCircle;
      default:
        return Clock;
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'success':
        return 'text-green-500';
      case 'failed':
        return 'text-red-500';
      default:
        return 'text-yellow-500';
    }
  }

  function formatDate(dateStr: string) {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(date);
  }

  function formatValue(value: any): string {
    if (Array.isArray(value)) {
      return value.length > 3
        ? `${value.slice(0, 3).join(', ')} and ${value.length - 3} more`
        : value.join(', ');
    }
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  }

  function formatKey(key: string): string {
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (l) => l.toUpperCase());
  }
</script>

{#if executions.length === 0}
  <div class="text-center py-12">
    <Clock class="h-12 w-12 mx-auto text-muted-foreground mb-4" />
    <h3 class="text-lg font-semibold mb-2">No executions yet</h3>
    <p class="text-muted-foreground">
      This task hasn't been executed yet. It will run according to its schedule.
    </p>
  </div>
{:else}
  <div class="space-y-4">
    {#each executions as execution (execution.id)}
      <Card
        class={highlightNotifications && execution.condition_met
          ? 'border-primary bg-primary/5'
          : ''}
      >
        <div class="p-4">
          <div class="flex items-start gap-4">
            <div class="shrink-0 mt-1">
              <svelte:component
                this={getStatusIcon(execution.status)}
                class="h-5 w-5 {getStatusColor(execution.status)}"
              />
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-2 flex-wrap">
                <Badge
                  variant={execution.status === 'success'
                    ? 'default'
                    : execution.status === 'failed'
                    ? 'destructive'
                    : 'secondary'}
                >
                  {execution.status}
                </Badge>

                {#if execution.condition_met}
                  <Badge variant="default">
                    <AlertCircle class="mr-1 h-3 w-3" />
                    Condition Met
                  </Badge>
                {/if}

                <span class="text-sm text-muted-foreground ml-auto">
                  {formatDate(execution.started_at)}
                </span>
              </div>

              {#if execution.change_summary}
                <div class="p-3 bg-muted rounded-md mb-3">
                  <p class="text-sm">
                    <span class="font-medium">What Changed: </span>
                    {execution.change_summary}
                  </p>
                </div>
              {/if}

              {#if execution.result?.answer}
                <div class="mb-3">
                  <div class="text-sm prose prose-sm max-w-none">
                    {@html execution.result.answer.replace(/\n/g, '<br>')}
                  </div>
                </div>
              {/if}

              {#if execution.result?.current_state}
                <div class="mb-3 p-3 bg-muted rounded-md">
                  <p class="text-sm font-medium mb-3">Current State:</p>
                  <div class="text-sm text-muted-foreground space-y-2">
                    {#each Object.entries(execution.result.current_state) as [key, value]}
                      <div>
                        <span class="font-medium text-foreground">
                          {formatKey(key)}:
                        </span>{' '}
                        <span class="text-xs">{formatValue(value)}</span>
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}

              {#if execution.grounding_sources.length > 0}
                <div>
                  <p class="text-sm mb-2">Grounding Sources:</p>
                  <div class="space-y-2">
                    {#each execution.grounding_sources as source}
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        class="flex items-start gap-2 p-2 rounded-md hover:bg-muted transition-colors group"
                      >
                        <ExternalLink class="h-4 w-4 shrink-0 mt-0.5 text-muted-foreground group-hover:text-primary" />
                        <div class="flex-1 min-w-0">
                          <p class="text-sm group-hover:text-primary truncate">
                            {source.title}
                          </p>
                          <p class="text-xs text-muted-foreground truncate">
                            {source.url}
                          </p>
                        </div>
                      </a>
                    {/each}
                  </div>
                </div>
              {/if}

              {#if execution.error_message}
                <div class="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                  <p class="text-sm text-destructive">
                    <span class="font-medium">Error: </span>
                    {execution.error_message}
                  </p>
                </div>
              {/if}
            </div>
          </div>
        </div>
      </Card>
    {/each}
  </div>
{/if}
