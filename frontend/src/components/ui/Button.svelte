<script lang="ts">
  import { cn } from '@/lib/utils';

  type Variant = 'default' | 'outline' | 'ghost' | 'destructive';
  type Size = 'default' | 'sm' | 'lg' | 'icon';

  export let variant: Variant = 'default';
  export let size: Size = 'default';
  export let disabled = false;
  export let type: 'button' | 'submit' | 'reset' = 'button';

  const variantClasses = {
    default: 'bg-primary text-primary-foreground hover:bg-primary/90',
    outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
    ghost: 'hover:bg-accent hover:text-accent-foreground',
    destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
  };

  const sizeClasses = {
    default: 'h-10 px-4 py-2',
    sm: 'h-9 px-3 text-sm',
    lg: 'h-11 px-8',
    icon: 'h-10 w-10',
  };

  $: className = cn(
    'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
    variantClasses[variant],
    sizeClasses[size]
  );
</script>

<button
  {type}
  class={className}
  {disabled}
  on:click
>
  <slot />
</button>
