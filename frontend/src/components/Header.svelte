<script lang="ts">
  import { Bell } from 'lucide-svelte';
  import { clerkUser, clerk } from '@/lib/clerk';
  import { onMount } from 'svelte';

  let userButtonMounted = false;

  onMount(() => {
    setTimeout(() => {
      const userButtonElement = document.getElementById('clerk-user-button');
      if (userButtonElement && !userButtonMounted) {
        clerk.mountUserButton(userButtonElement);
        userButtonMounted = true;
      }
    }, 100);
  });
</script>

<header class="border-b">
  <div class="container mx-auto px-4 h-16 flex items-center justify-between">
    <div class="flex items-center gap-2">
      <Bell class="h-6 w-6 text-primary" />
      <h2 class="text-xl font-semibold">Torale</h2>
    </div>

    <div class="flex items-center gap-4">
      {#if $clerkUser}
        <span class="text-sm text-muted-foreground hidden sm:inline">
          {$clerkUser.primaryEmailAddress?.emailAddress}
        </span>
      {/if}
      <div id="clerk-user-button"></div>
    </div>
  </div>
</header>
