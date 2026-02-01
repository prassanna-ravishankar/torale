import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { Task, NotifyBehavior } from '@/types';
import {
  Loader2,
  Sparkles,
  Search,
  Bell,
  AlertCircle,
  Globe,
  Lock,
  Copy,
  Eye,
  Users
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { BrutalistSwitch } from "@/components/torale";
import { UsernamePickerModal } from "@/components/UsernamePickerModal";
import { useAuth } from '@/contexts/AuthContext';

interface TaskEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task | null;
  onSuccess: (task: Task) => void;
}

const MIN_NAME_LENGTH = 3;
const MIN_SEARCH_QUERY_LENGTH = 10;
const MIN_CONDITION_DESCRIPTION_LENGTH = 10;

export const TaskEditDialog: React.FC<TaskEditDialogProps> = ({
  open,
  onOpenChange,
  task,
  onSuccess,
}) => {
  // Form data
  const [name, setName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [conditionDescription, setConditionDescription] = useState('');
  const [notifyBehavior, setNotifyBehavior] = useState<NotifyBehavior>('once');

  // UI state
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Magic Input state
  const [magicPrompt, setMagicPrompt] = useState("");
  const [isMagicLoading, setIsMagicLoading] = useState(false);

  // Sharing state
  const [isPublic, setIsPublic] = useState(false);
  const [isTogglingVisibility, setIsTogglingVisibility] = useState(false);
  const [showUsernameModal, setShowUsernameModal] = useState(false);
  const { user } = useAuth();

  // Load task data when task changes
  useEffect(() => {
    if (task && open) {
      setName(task.name);
      setSearchQuery(task.search_query || '');
      setConditionDescription(task.condition_description || '');
      setNotifyBehavior(task.notify_behavior as NotifyBehavior);
      setIsPublic(task.is_public);
    }
  }, [task, open]);

  // Reset on close
  useEffect(() => {
    if (!open) {
      setValidationErrors({});
      setError("");
      setMagicPrompt("");
      setIsMagicLoading(false);
    }
  }, [open]);

  const handleSuggest = async () => {
    if (!magicPrompt.trim()) return;

    setIsMagicLoading(true);
    try {
      const suggestion = await api.suggestTask(magicPrompt, {
        name,
        search_query: searchQuery,
        condition_description: conditionDescription,
        schedule: task?.schedule || "0 */6 * * *",
        notify_behavior: notifyBehavior,
        state: "active"
      });

      setName(suggestion.name);
      setSearchQuery(suggestion.search_query);
      setConditionDescription(suggestion.condition_description);
      // Use suggested notify_behavior if it's once or always
      const behavior = suggestion.notify_behavior as NotifyBehavior;
      if (behavior === "once" || behavior === "always") {
        setNotifyBehavior(behavior);
      }

      toast.success("Task configuration updated from suggestion!");
    } catch (error) {
      console.error("Magic suggestion failed:", error);
      toast.error("Failed to generate task configuration");
    } finally {
      setIsMagicLoading(false);
    }
  };

  const handleVisibilityToggle = async (checked: boolean) => {
    if (!task) return;

    if (checked && !user?.username) {
      setShowUsernameModal(true);
      return;
    }

    setIsTogglingVisibility(true);
    try {
      const result = await api.updateTaskVisibility(task.id, checked);
      setIsPublic(result.is_public);

      if (result.is_public && result.slug) {
        const vanityUrl = `${window.location.origin}/t/${user?.username}/${result.slug}`;
        toast.success(`Task is now public: ${vanityUrl}`);
      } else {
        toast.success('Task is now private');
      }

      onSuccess({ ...task, is_public: result.is_public, slug: result.slug });
    } catch (error) {
      console.error('Failed to toggle visibility:', error);
      toast.error('Failed to update task visibility');
    } finally {
      setIsTogglingVisibility(false);
    }
  };

  const handleUsernameSet = async (username: string) => {
    if (task) {
      setIsTogglingVisibility(true);
      try {
        const result = await api.updateTaskVisibility(task.id, true);
        setIsPublic(result.is_public);

        if (result.is_public && result.slug) {
          const vanityUrl = `${window.location.origin}/t/${username}/${result.slug}`;
          toast.success(`Task is now public: ${vanityUrl}`);
        }

        onSuccess({ ...task, is_public: result.is_public, slug: result.slug });
      } catch (error) {
        console.error('Failed to make task public:', error);
        toast.error('Failed to make task public');
      } finally {
        setIsTogglingVisibility(false);
      }
    }
  };

  const copyVanityUrl = () => {
    if (task?.slug && user?.username) {
      const vanityUrl = `${window.location.origin}/t/${user.username}/${task.slug}`;
      navigator.clipboard.writeText(vanityUrl);
      toast.success('Link copied to clipboard!');
    }
  };

  // Validation
  const validate = (): boolean => {
    const errors: Record<string, string> = {};

    if (!name.trim()) {
      errors.name = "Task name is required";
    } else if (name.length < MIN_NAME_LENGTH) {
      errors.name = `Task name must be at least ${MIN_NAME_LENGTH} characters`;
    }

    if (!searchQuery.trim()) {
      errors.searchQuery = "Search query is required";
    } else if (searchQuery.length < MIN_SEARCH_QUERY_LENGTH) {
      errors.searchQuery = "Please provide a more specific search query";
    }

    if (!conditionDescription.trim()) {
      errors.conditionDescription = "Trigger condition is required";
    } else if (conditionDescription.length < MIN_CONDITION_DESCRIPTION_LENGTH) {
      errors.conditionDescription = "Please provide a more specific condition";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Update task
  const handleUpdate = async () => {
    if (!task) return;

    if (!validate()) {
      toast.error("Please fix the errors before updating");
      return;
    }

    setError("");
    setIsUpdating(true);

    try {
      const updatedTask = await api.updateTask(task.id, {
        name,
        search_query: searchQuery,
        condition_description: conditionDescription,
        notify_behavior: notifyBehavior,
        // Preserve existing schedule — agent controls this via next_run
      });

      toast.success('Task updated successfully');
      onSuccess(updatedTask);
      onOpenChange(false);
    } catch (err) {
      console.error('Failed to update task:', err);
      const errorMessage = err instanceof Error ? err.message : "Failed to update task";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsUpdating(false);
    }
  };

  if (!task) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col overflow-hidden border-2 border-zinc-900 shadow-brutalist-lg">
        <DialogHeader className="flex-shrink-0 border-b-2 border-zinc-100 pb-4">
          <DialogTitle className="text-2xl font-bold font-grotesk tracking-tight">
            Edit Monitor
          </DialogTitle>
          <DialogDescription className="text-zinc-500">
            Update your monitoring task settings
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Magic Input Section */}
          <div className="bg-zinc-50 p-4 border-2 border-zinc-200 space-y-3">
            <div className="flex items-center gap-2 text-sm font-bold font-grotesk text-zinc-900">
              <Sparkles className="w-4 h-4" />
              Magic Refine
            </div>
            <div className="flex gap-2">
              <Input
                placeholder="Describe how you want to change this task..."
                value={magicPrompt}
                onChange={(e) => setMagicPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSuggest();
                  }
                }}
                className="flex-1 bg-background"
              />
              <Button
                onClick={handleSuggest}
                disabled={!magicPrompt.trim() || isMagicLoading}
                variant="secondary"
                className="shrink-0"
              >
                {isMagicLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                {isMagicLoading ? "Thinking..." : "Refine"}
              </Button>
            </div>
          </div>

          <div className="space-y-4">
            {/* Task Name */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider">Monitor Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (validationErrors.name) setValidationErrors(prev => ({ ...prev, name: "" }));
                }}
                disabled={isUpdating}
                className={cn(validationErrors.name && "border-destructive")}
              />
              {validationErrors.name && (
                <p className="text-xs text-destructive flex items-center gap-1.5">
                  <AlertCircle className="h-3 w-3" />
                  {validationErrors.name}
                </p>
              )}
            </div>

            {/* Search Query */}
            <div className="space-y-2">
              <Label htmlFor="searchQuery" className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider flex items-center gap-2">
                <Search className="h-3 w-3" />
                What to Monitor
              </Label>
              <Textarea
                id="searchQuery"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  if (validationErrors.searchQuery) setValidationErrors(prev => ({ ...prev, searchQuery: "" }));
                }}
                disabled={isUpdating}
                rows={3}
                className={cn("resize-none", validationErrors.searchQuery && "border-destructive")}
              />
              {validationErrors.searchQuery && (
                <p className="text-xs text-destructive flex items-center gap-1.5">
                  <AlertCircle className="h-3 w-3" />
                  {validationErrors.searchQuery}
                </p>
              )}
            </div>

            {/* Condition Description */}
            <div className="space-y-2">
              <Label htmlFor="condition" className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider flex items-center gap-2">
                <Bell className="h-3 w-3" />
                When to Notify
              </Label>
              <Textarea
                id="condition"
                value={conditionDescription}
                onChange={(e) => {
                  setConditionDescription(e.target.value);
                  if (validationErrors.conditionDescription) setValidationErrors(prev => ({ ...prev, conditionDescription: "" }));
                }}
                disabled={isUpdating}
                rows={3}
                className={cn("resize-none", validationErrors.conditionDescription && "border-destructive")}
              />
              {validationErrors.conditionDescription && (
                <p className="text-xs text-destructive flex items-center gap-1.5">
                  <AlertCircle className="h-3 w-3" />
                  {validationErrors.conditionDescription}
                </p>
              )}
            </div>

            {/* Notification Mode - inline toggle */}
            <div className="flex items-center gap-3 p-3 bg-zinc-50 border-2 border-zinc-100">
              <Bell className="h-4 w-4 text-zinc-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <Label className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider block mb-1">
                  Notification Mode
                </Label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setNotifyBehavior("once")}
                    className={cn(
                      "text-xs px-3 py-1.5 border-2 font-mono transition-colors",
                      notifyBehavior === "once"
                        ? "border-zinc-900 bg-zinc-900 text-white"
                        : "border-zinc-200 text-zinc-600 hover:border-zinc-400"
                    )}
                  >
                    Notify once then stop
                  </button>
                  <button
                    type="button"
                    onClick={() => setNotifyBehavior("always")}
                    className={cn(
                      "text-xs px-3 py-1.5 border-2 font-mono transition-colors",
                      notifyBehavior === "always"
                        ? "border-zinc-900 bg-zinc-900 text-white"
                        : "border-zinc-200 text-zinc-600 hover:border-zinc-400"
                    )}
                  >
                    Keep monitoring
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Sharing Section */}
          <div className="space-y-4 p-4 bg-zinc-50 border-2 border-zinc-200">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  {isPublic ? (
                    <Globe className="h-4 w-4 text-blue-600" />
                  ) : (
                    <Lock className="h-4 w-4 text-zinc-500" />
                  )}
                  <Label className="text-sm font-medium">
                    {isPublic ? 'Public Task' : 'Private Task'}
                  </Label>
                </div>
                <p className="text-xs text-muted-foreground">
                  {isPublic
                    ? 'Anyone can view and copy this task'
                    : 'Only you can see this task'}
                </p>
              </div>
              <BrutalistSwitch
                checked={isPublic}
                onCheckedChange={handleVisibilityToggle}
                disabled={isTogglingVisibility}
              />
            </div>

            {/* Public task details */}
            {isPublic && task?.slug && user?.username && (
              <div className="space-y-3 pt-2 border-t border-zinc-200">
                <div className="space-y-2">
                  <Label className="text-xs text-zinc-500">Public Link</Label>
                  <div className="flex gap-2">
                    <Input
                      value={`${window.location.origin}/t/${user.username}/${task.slug}`}
                      readOnly
                      className="font-mono text-sm bg-background"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={copyVanityUrl}
                      className="shrink-0"
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Stats */}
                {(task.view_count > 0 || task.subscriber_count > 0) && (
                  <div className="flex items-center gap-4 text-sm text-zinc-600">
                    <div className="flex items-center gap-1.5">
                      <Eye className="h-4 w-4" />
                      <span>{task.view_count} views</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Users className="h-4 w-4" />
                      <span>{task.subscriber_count} forks</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter className="pt-4 border-t-2 border-zinc-100 flex-shrink-0 gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isUpdating}>
            Cancel
          </Button>
          <Button onClick={handleUpdate} disabled={isUpdating} className="shadow-brutalist">
            {isUpdating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>

      {/* Username Picker Modal */}
      <UsernamePickerModal
        isOpen={showUsernameModal}
        onClose={() => setShowUsernameModal(false)}
        onSuccess={handleUsernameSet}
      />
    </Dialog>
  );
};
