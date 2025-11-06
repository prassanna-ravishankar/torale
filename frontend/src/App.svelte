<script lang="ts">
  import { Router, Route, navigate } from 'svelte-routing';
  import { onMount } from 'svelte';
  import { Toaster } from 'svelte-sonner';
  import { initializeClerk, clerkLoaded, isSignedIn, clerk } from './lib/clerk';

  import Dashboard from './components/Dashboard.svelte';
  import TaskDetail from './components/TaskDetail.svelte';
  import Header from './components/Header.svelte';
  import Loader from './components/Loader.svelte';

  let mounted = false;

  onMount(async () => {
    await initializeClerk();
    mounted = true;
  });

  // Redirect logic based on authentication state
  $: if ($clerkLoaded && !$isSignedIn && window.location.pathname !== '/sign-in' && window.location.pathname !== '/sign-up') {
    navigate('/sign-in');
  }

  function handleTaskClick(taskId: string) {
    navigate(`/tasks/${taskId}`);
  }

  function handleBackToDashboard() {
    navigate('/');
  }

  // Mount Clerk components when elements are available
  $: if (mounted && $clerkLoaded && !$isSignedIn) {
    setTimeout(() => {
      const signinEl = document.getElementById('clerk-signin');
      const signupEl = document.getElementById('clerk-signup');
      if (signinEl) clerk.mountSignIn(signinEl);
      if (signupEl) clerk.mountSignUp(signupEl);
    }, 100);
  }
</script>

<Router>
  <Route path="/sign-in">
    {#if !$clerkLoaded}
      <div class="min-h-screen flex items-center justify-center">
        <Loader />
      </div>
    {:else if $isSignedIn}
      <script>navigate('/');</script>
      <div class="min-h-screen flex items-center justify-center">
        <Loader />
      </div>
    {:else}
      <div class="min-h-screen flex items-center justify-center bg-muted/30">
        <div id="clerk-signin"></div>
      </div>
    {/if}
  </Route>

  <Route path="/sign-up">
    {#if !$clerkLoaded}
      <div class="min-h-screen flex items-center justify-center">
        <Loader />
      </div>
    {:else if $isSignedIn}
      <script>navigate('/');</script>
      <div class="min-h-screen flex items-center justify-center">
        <Loader />
      </div>
    {:else}
      <div class="min-h-screen flex items-center justify-center bg-muted/30">
        <div id="clerk-signup"></div>
      </div>
    {/if}
  </Route>

  <Route path="/">
    {#if !$clerkLoaded}
      <div class="min-h-screen flex items-center justify-center">
        <Loader />
      </div>
    {:else if !$isSignedIn}
      <div class="min-h-screen flex items-center justify-center">
        <Loader />
      </div>
    {:else}
      <div class="min-h-screen bg-background">
        <Header />
        <main class="container mx-auto px-4 py-8">
          <Dashboard onTaskClick={handleTaskClick} />
        </main>
      </div>
    {/if}
  </Route>

  <Route path="/tasks/:taskId" let:params>
    {#if !$clerkLoaded}
      <div class="min-h-screen flex items-center justify-center">
        <Loader />
      </div>
    {:else if !$isSignedIn}
      <div class="min-h-screen flex items-center justify-center">
        <Loader />
      </div>
    {:else}
      <div class="min-h-screen bg-background">
        <Header />
        <main class="container mx-auto px-4 py-8">
          <TaskDetail taskId={params.taskId} onBack={handleBackToDashboard} onDeleted={handleBackToDashboard} />
        </main>
      </div>
    {/if}
  </Route>
</Router>

<Toaster />
