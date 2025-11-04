import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { NotifyBehavior } from "@/types";
import api from "@/lib/api";
import { Loader2, Info } from "lucide-react";
import { Alert } from "@/components/ui/alert";
import { toast } from 'sonner';

interface TaskCreationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated: () => void;
}

const SCHEDULE_OPTIONS = [
  { value: "*/30 * * * *", label: "Every 30 minutes" },
  { value: "0 */6 * * *", label: "Every 6 hours" },
  { value: "0 9 * * *", label: "Every day at 9:00 AM" },
  { value: "0 12 * * *", label: "Every day at noon" },
  { value: "0 8 * * 1", label: "Every Monday at 8:00 AM" },
  { value: "0 0 * * 0", label: "Every Sunday at midnight" },
];

export const TaskCreationDialog: React.FC<TaskCreationDialogProps> = ({
  open,
  onOpenChange,
  onTaskCreated,
}) => {
  const [name, setName] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [conditionDescription, setConditionDescription] = useState("");
  const [schedule, setSchedule] = useState("0 9 * * *");
  const [notifyBehavior, setNotifyBehavior] = useState<NotifyBehavior>("track_state");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await api.createTask({
        name,
        search_query: searchQuery,
        condition_description: conditionDescription,
        schedule,
        notify_behavior: notifyBehavior,
        executor_type: "llm_grounded_search",
        is_active: true,
      });

      toast.success('Task created successfully');

      // Reset form
      setName("");
      setSearchQuery("");
      setConditionDescription("");
      setSchedule("0 9 * * *");
      setNotifyBehavior("track_state");

      onTaskCreated();
      onOpenChange(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create task";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Monitoring Task</DialogTitle>
          <DialogDescription>
            Set up AI-powered monitoring for any web-based information
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name">Task Name</Label>
            <Input
              id="name"
              placeholder="e.g., iPhone 16 Release Date"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              A descriptive name to identify this monitoring task
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="searchQuery">Search Query</Label>
            <Textarea
              id="searchQuery"
              placeholder="e.g., When is the next iPhone being announced?"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              required
              disabled={isLoading}
              rows={3}
            />
            <p className="text-xs text-muted-foreground">
              What should we search for? Be specific and use natural language.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="condition">Trigger Condition</Label>
            <Textarea
              id="condition"
              placeholder="e.g., A specific release date is announced"
              value={conditionDescription}
              onChange={(e) => setConditionDescription(e.target.value)}
              required
              disabled={isLoading}
              rows={2}
            />
            <p className="text-xs text-muted-foreground">
              When should we notify you? Describe the condition that matters to you.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="schedule">Check Frequency</Label>
            <Select value={schedule} onValueChange={setSchedule} disabled={isLoading}>
              <SelectTrigger id="schedule">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SCHEDULE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              How often should we check for updates?
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="notifyBehavior">Notification Behavior</Label>
            <Select
              value={notifyBehavior}
              onValueChange={(value) => setNotifyBehavior(value as NotifyBehavior)}
              disabled={isLoading}
            >
              <SelectTrigger id="notifyBehavior">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="once">
                  Notify Once (stop after first match)
                </SelectItem>
                <SelectItem value="always">
                  Always Notify (every time condition is met)
                </SelectItem>
                <SelectItem value="track_state">
                  Track State Changes (notify when information changes)
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              How should we handle repeated notifications?
            </p>
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <div className="ml-2">
              <p className="text-sm">
                The AI will search the web, analyze results, and notify you when your
                condition is met. All findings include source links for verification.
              </p>
            </div>
          </Alert>

          {error && <Alert variant="destructive">{error}</Alert>}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Task
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
