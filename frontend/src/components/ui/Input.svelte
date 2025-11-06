<script lang="ts">
  import { cn } from '@/lib/utils';

  export let value = '';
  export let type = 'text';
  export let placeholder = '';
  export let disabled = false;
  export let required = false;
  export let id = '';

  let className = '';
  export { className as class };
</script>

<input
  {type}
  {placeholder}
  {disabled}
  {required}
  {id}
  bind:value
  class={cn(
    'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
    className
  )}
  on:input
  on:change
  on:keydown
/>
