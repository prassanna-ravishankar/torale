<script lang="ts">
  export let open = false;
  export let onOpenChange: (open: boolean) => void;

  function handleClose() {
    onOpenChange(false);
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  }
</script>

{#if open}
  <div
    class="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
    on:click={handleBackdropClick}
    on:keydown={(e) => e.key === 'Escape' && handleClose()}
    role="button"
    tabindex="0"
  >
    <div class="fixed left-[50%] top-[50%] z-50 translate-x-[-50%] translate-y-[-50%] w-full max-w-lg">
      <div class="bg-background p-6 shadow-lg rounded-lg border">
        <slot />
      </div>
    </div>
  </div>
{/if}
