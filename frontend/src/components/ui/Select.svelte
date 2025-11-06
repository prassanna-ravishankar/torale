<script lang="ts">
  import { cn } from '@/lib/utils';

  export let value = '';
  export let disabled = false;
  export let id = '';

  let className = '';
  export { className as class };
</script>

<select
  bind:value
  {disabled}
  {id}
  class={cn(
    'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
    className
  )}
  on:change
>
  <slot />
</select>
