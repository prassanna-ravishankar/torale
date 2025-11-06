<script lang="ts">
  import { Dialog as DialogPrimitive } from "bits-ui";
  import { cn } from "@/lib/utils";
  import { fade, scale } from "svelte/transition";

  export let open = false;
  export let onOpenChange: ((open: boolean) => void) | undefined = undefined;

  $: if (onOpenChange) {
    onOpenChange(open);
  }
</script>

<DialogPrimitive.Root bind:open>
  <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay
      transition={fade}
      transitionConfig={{ duration: 150 }}
      class="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
    />
    <DialogPrimitive.Content
      transition={scale}
      transitionConfig={{ duration: 150, start: 0.95 }}
      class={cn(
        "fixed left-[50%] top-[50%] z-50 translate-x-[-50%] translate-y-[-50%] w-full max-w-lg bg-background p-6 shadow-lg rounded-lg border",
        $$props.class
      )}
    >
      <slot />
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
</DialogPrimitive.Root>
