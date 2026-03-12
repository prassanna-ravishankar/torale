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
import { getTaskShareUrl } from '@/lib/utils';
import type { Task } from '@/types';
import {
  Loader2,
  Search,
  AlertCircle,
  Globe,
  Lock,
  Copy,
  Eye,
  Users
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn, getErrorMessage } from '@/lib/utils';
import { BrutalistSwitch, FieldError } from "@/components/torale";

interface TaskEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task | null;
  onSuccess: (task: Task) => void;
}

const MIN_NAME_LENGTH = 3;
const MIN_INSTRUCTIONS_LENGTH = 10;

export const TaskEditDialog: React.FC<TaskEditDialogProps> = ({
  open,
  onOpenChange,
  task,
  onSuccess,
}) => {
  // Form data
  const [name, setName] = useState('');
  const [instructions, setInstructions] = useState('');

  // UI state
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Sharing state
  const [isPublic, setIsPublic] = useState(false);
  const [isTogglingVisibility, setIsTogglingVisibility] = useState(false);

  // Load task data when task changes
  useEffect(() => {
    if (task && open) {
      setName(task.name);
      setInstructions(task.search_query || '');
      setIsPublic(task.is_public);
    }
  }, [task, open]);

  // Reset on close
  useEffect(() => {
    if (!open) {
      setValidationErrors({});
      setError("");
    }
  }, [open]);


  const handleVisibilityToggle = async (checked: boolean) => {
    if (!task) return;

    setIsTogglingVisibility(true);
    try {
      const result = await api.updateTaskVisibility(task.id, checked);
      setIsPublic(result.is_public);

      if (result.is_public) {
        const shareUrl = getTaskShareUrl(task.id);
        toast.success(`Task is now public: ${shareUrl}`);
      } else {
        toast.success('Task is now private');
      }

      onSuccess({ ...task, is_public: result.is_public });
    } catch (error) {
      console.error('Failed to toggle visibility:', error);
      toast.error('Failed to update task visibility');
    } finally {
      setIsTogglingVisibility(false);
    }
  };

  const copyShareUrl = () => {
    if (task) {
      const shareUrl = getTaskShareUrl(task.id);
      navigator.clipboard.writeText(shareUrl);
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

    if (!instructions.trim()) {
      errors.instructions = "Please describe what to monitor";
    } else if (instructions.length < MIN_INSTRUCTIONS_LENGTH) {
      errors.instructions = "Please provide more detail";
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
        search_query: instructions,
      });

      toast.success('Task updated successfully');
      onSuccess(updatedTask);
      onOpenChange(false);
    } catch (err) {
      console.error('Failed to update task:', err);
      const errorMessage = getErrorMessage(err, "Failed to update task");
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
              <FieldError message={validationErrors.name} />
            </div>

            {/* What to Monitor */}
            <div className="space-y-2">
              <Label htmlFor="instructions" className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider flex items-center gap-2">
                <Search className="h-3 w-3" />
                What to Monitor
              </Label>
              <Textarea
                id="instructions"
                value={instructions}
                onChange={(e) => {
                  setInstructions(e.target.value);
                  if (validationErrors.instructions) setValidationErrors(prev => ({ ...prev, instructions: "" }));
                }}
                disabled={isUpdating}
                rows={6}
                className={cn("resize-none", validationErrors.instructions && "border-destructive")}
              />
              <FieldError message={validationErrors.instructions} />
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
            {isPublic && (
              <div className="space-y-3 pt-2 border-t border-zinc-200">
                <div className="space-y-2">
                  <Label className="text-xs text-zinc-500">Public Link</Label>
                  <div className="flex gap-2">
                    <Input
                      value={getTaskShareUrl(task.id)}
                      readOnly
                      className="font-mono text-sm bg-background"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={copyShareUrl}
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
    </Dialog>
  );
};
