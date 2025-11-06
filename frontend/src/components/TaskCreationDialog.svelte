<script lang="ts">
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { api } from '@/lib/apiClient';
  import type { NotifyBehavior, TaskTemplate } from '@/lib/types';

  import Dialog from './ui/dialog.svelte';
  import Button from './ui/button.svelte';
  import Input from './ui/input.svelte';
  import Label from './ui/label.svelte';
  import Textarea from './ui/textarea.svelte';
  import Select from './ui/select.svelte';
  import { Loader2, Info, Sparkles } from 'lucide-svelte';

  export let open = false;
  export let onOpenChange: (open: boolean) => void;
  export let onTaskCreated: () => void;

  const SCHEDULE_OPTIONS = [
    { value: '*/30 * * * *', label: 'Every 30 minutes' },
    { value: '0 */6 * * *', label: 'Every 6 hours' },
    { value: '0 9 * * *', label: 'Every day at 9:00 AM' },
    { value: '0 12 * * *', label: 'Every day at noon' },
    { value: '0 8 * * 1', label: 'Every Monday at 8:00 AM' },
    { value: '0 0 * * 0', label: 'Every Sunday at midnight' },
  ];

  let templates: TaskTemplate[] = [];
  let selectedTemplateId = 'none';
  let name = '';
  let searchQuery = '';
  let conditionDescription = '';
  let schedule = '0 9 * * *';
  let notifyBehavior: NotifyBehavior = 'track_state';
  let isLoading = false;
  let error = '';

  onMount(async () => {
    try {
      const data = await api.getTemplates();
      templates = data;
    } catch (err) {
      console.error('Failed to load templates:', err);
    }
  });

  $: if (selectedTemplateId && selectedTemplateId !== 'none') {
    const template = templates.find((t) => t.id === selectedTemplateId);
    if (template) {
      name = template.name;
      searchQuery = template.search_query;
      conditionDescription = template.condition_description;
      schedule = template.schedule;
      notifyBehavior = template.notify_behavior;
    }
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    error = '';
    isLoading = true;

    try {
      await api.createTask({
        name,
        search_query: searchQuery,
        condition_description: conditionDescription,
        schedule,
        notify_behavior: notifyBehavior,
        executor_type: 'llm_grounded_search',
        config: {
          model: 'gemini-2.0-flash-exp',
          search_provider: 'google',
        },
        is_active: true,
      });

      toast.success('Task created successfully');

      // Reset form
      selectedTemplateId = 'none';
      name = '';
      searchQuery = '';
      conditionDescription = '';
      schedule = '0 9 * * *';
      notifyBehavior = 'track_state';

      onTaskCreated();
      onOpenChange(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create task';
      error = errorMessage;
      toast.error(errorMessage);
    } finally {
      isLoading = false;
    }
  }

  // Group templates by category
  $: groupedTemplates = templates.reduce((acc, template) => {
    if (!acc[template.category]) {
      acc[template.category] = [];
    }
    acc[template.category].push(template);
    return acc;
  }, {} as Record<string, TaskTemplate[]>);
</script>

<Dialog {open} {onOpenChange}>
  <div class="space-y-4">
    <div>
      <h2 class="text-lg font-semibold">Create Monitoring Task</h2>
      <p class="text-sm text-muted-foreground">
        Set up AI-powered monitoring for any web-based information
      </p>
    </div>

    <form on:submit={handleSubmit} class="space-y-6">
      {#if templates.length > 0}
        <div class="space-y-2 pb-4 border-b">
          <Label htmlFor="template" class="flex items-center gap-2">
            <Sparkles class="h-4 w-4 text-purple-500" />
            Start from Template (Optional)
          </Label>
          <Select id="template" bind:value={selectedTemplateId}>
            <option value="none">Create from scratch</option>
            {#each Object.entries(groupedTemplates) as [category, categoryTemplates]}
              <optgroup label={category}>
                {#each categoryTemplates as template}
                  <option value={template.id}>
                    {template.icon ? `${template.icon} ` : ''}{template.name}
                  </option>
                {/each}
              </optgroup>
            {/each}
          </Select>
          <p class="text-xs text-muted-foreground">
            Select a template to auto-fill the form, then customize as needed
          </p>
        </div>
      {/if}

      <div class="space-y-2">
        <Label htmlFor="name">Task Name</Label>
        <Input
          id="name"
          placeholder="e.g., iPhone 16 Release Date"
          bind:value={name}
          required
          disabled={isLoading}
        />
        <p class="text-xs text-muted-foreground">
          A descriptive name to identify this monitoring task
        </p>
      </div>

      <div class="space-y-2">
        <Label htmlFor="searchQuery">Search Query</Label>
        <Textarea
          id="searchQuery"
          placeholder="e.g., When is the next iPhone being announced?"
          bind:value={searchQuery}
          required
          disabled={isLoading}
          rows={3}
        />
        <p class="text-xs text-muted-foreground">
          What should we search for? Be specific and use natural language.
        </p>
      </div>

      <div class="space-y-2">
        <Label htmlFor="condition">Trigger Condition</Label>
        <Textarea
          id="condition"
          placeholder="e.g., A specific release date is announced"
          bind:value={conditionDescription}
          required
          disabled={isLoading}
          rows={2}
        />
        <p class="text-xs text-muted-foreground">
          When should we notify you? Describe the condition that matters to you.
        </p>
      </div>

      <div class="space-y-2">
        <Label htmlFor="schedule">Check Frequency</Label>
        <Select id="schedule" bind:value={schedule} disabled={isLoading}>
          {#each SCHEDULE_OPTIONS as option}
            <option value={option.value}>{option.label}</option>
          {/each}
        </Select>
        <p class="text-xs text-muted-foreground">
          How often should we check for updates?
        </p>
      </div>

      <div class="space-y-2">
        <Label htmlFor="notifyBehavior">Notification Behavior</Label>
        <Select id="notifyBehavior" bind:value={notifyBehavior} disabled={isLoading}>
          <option value="once">Notify Once (stop after first match)</option>
          <option value="always">Always Notify (every time condition is met)</option>
          <option value="track_state">Track State Changes (notify when information changes)</option>
        </Select>
        <p class="text-xs text-muted-foreground">
          How should we handle repeated notifications?
        </p>
      </div>

      <div class="flex items-center gap-2 p-4 rounded-lg border bg-card">
        <Info class="h-4 w-4 shrink-0" />
        <p class="text-sm">
          The AI will search the web, analyze results, and notify you when your condition is met. All findings include source links for verification.
        </p>
      </div>

      {#if error}
        <div class="p-4 rounded-lg border border-destructive bg-destructive/10 text-destructive text-sm">
          {error}
        </div>
      {/if}

      <div class="flex gap-2 justify-end">
        <Button type="button" variant="outline" on:click={() => onOpenChange(false)} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {#if isLoading}
            <Loader2 class="mr-2 h-4 w-4 animate-spin" />
          {/if}
          Create Task
        </Button>
      </div>
    </form>
  </div>
</Dialog>
