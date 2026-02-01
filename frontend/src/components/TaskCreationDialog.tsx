import React, { useState, useEffect } from "react";
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
  SelectGroup,
  SelectLabel,
} from "@/components/ui/select";
import type { NotifyBehavior, TaskTemplate, Task } from "@/types";
import api from "@/lib/api";
import {
  Loader2,
  Sparkles,
  Search,
  Bell,
  AlertCircle,
  Music,
  Waves,
  Gamepad2,
  Code2,
  Bot,
  Cpu,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from 'sonner';
import { cn } from "@/lib/utils";

interface TaskCreationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated: (task: Task) => void;
}

// Icon mapping for templates
const iconMappings = [
  { keywords: ['concert', 'ticket', 'music'], icon: Music },
  { keywords: ['swimming', 'pool', 'summer'], icon: Waves },
  { keywords: ['ps5', 'playstation', 'stock'], icon: Gamepad2 },
  { keywords: ['framework', 'react', 'code'], icon: Code2 },
  { keywords: ['ai', 'gpt', 'model', 'robot'], icon: Bot },
  { keywords: ['gpu', 'graphics', 'cpu', 'nvidia'], icon: Cpu },
];

const getTemplateIcon = (templateName: string) => {
  const name = templateName.toLowerCase();
  const mapping = iconMappings.find(m => m.keywords.some(k => name.includes(k)));
  return mapping ? mapping.icon : Sparkles;
};

const MIN_NAME_LENGTH = 3;
const MIN_SEARCH_QUERY_LENGTH = 10;
const MIN_CONDITION_DESCRIPTION_LENGTH = 10;

export const TaskCreationDialog: React.FC<TaskCreationDialogProps> = ({
  open,
  onOpenChange,
  onTaskCreated,
}) => {
  // Form data
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("none");
  const [name, setName] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [conditionDescription, setConditionDescription] = useState("");
  const [notifyBehavior, setNotifyBehavior] = useState<NotifyBehavior>("once");

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Magic Input state
  const [magicPrompt, setMagicPrompt] = useState("");
  const [isMagicLoading, setIsMagicLoading] = useState(false);

  const handleSuggest = async () => {
    if (!magicPrompt.trim()) return;

    setIsMagicLoading(true);
    try {
      const suggestion = await api.suggestTask(magicPrompt);

      setName(suggestion.name);
      setSearchQuery(suggestion.search_query);
      setConditionDescription(suggestion.condition_description);
      // Use suggested notify_behavior if it's once or always (skip track_state for new tasks)
      const behavior = suggestion.notify_behavior as NotifyBehavior;
      if (behavior === "once" || behavior === "always") {
        setNotifyBehavior(behavior);
      }

      toast.success("Task configuration generated!");
    } catch (error) {
      console.error("Magic suggestion failed:", error);
      toast.error("Failed to generate task configuration");
    } finally {
      setIsMagicLoading(false);
    }
  };
  const [error, setError] = useState("");
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // Fetch templates on mount
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        const data = await api.getTemplates();
        setTemplates(data);
      } catch (err) {
        console.error("Failed to load templates:", err);
      }
    };
    loadTemplates();
  }, []);

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setSelectedTemplateId("none");
      setName("");
      setSearchQuery("");
      setConditionDescription("");
      setNotifyBehavior("once");
      setValidationErrors({});
      setError("");
      setMagicPrompt("");
      setIsMagicLoading(false);
    }
  }, [open]);

  // Auto-fill form when template is selected
  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);

    if (!templateId || templateId === "none") {
      return;
    }

    const template = templates.find(t => t.id === templateId);
    if (template) {
      setName(template.name);
      setSearchQuery(template.search_query);
      setConditionDescription(template.condition_description);
      // Map template notify_behavior to simplified options
      setNotifyBehavior(template.notify_behavior === "always" ? "always" : "once");
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

  // Task creation
  const handleCreateTask = async () => {
    if (!validate()) {
      toast.error("Please fix the errors before creating");
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      const newTask = await api.createTask({
        name,
        search_query: searchQuery,
        condition_description: conditionDescription,
        schedule: "0 */6 * * *",
        notify_behavior: notifyBehavior,
        state: "active",
        run_immediately: true,
      });

      onTaskCreated(newTask);
      onOpenChange(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create task";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleCreateTask();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col overflow-hidden border-2 border-zinc-900 shadow-brutalist-lg">
        <DialogHeader className="flex-shrink-0 border-b-2 border-zinc-100 pb-4">
          <DialogTitle className="text-2xl font-bold font-grotesk tracking-tight">
            Create Monitor
          </DialogTitle>
          <DialogDescription className="text-zinc-500">
            Define what you want to track and when to notify you
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Magic Input Section */}
          <div className="bg-zinc-50 p-4 border-2 border-zinc-200 space-y-3">
            <div className="flex items-center gap-2 text-sm font-bold font-grotesk text-zinc-900">
              <Sparkles className="w-4 h-4" />
              Magic Auto-Fill
            </div>
            <div className="flex gap-2">
              <Input
                placeholder="e.g. 'Notify me when PS5 Pro is in stock' or 'Tell me when GTA 6 release date is announced'"
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
                {isMagicLoading ? "Dreaming..." : "Auto-Fill"}
              </Button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">

            {/* Template Selection */}
            {templates.length > 0 && (
              <div className="bg-zinc-50 p-3 border-2 border-zinc-100">
                <Label className="text-[10px] font-mono uppercase text-zinc-400 mb-2 block tracking-wider">
                  Start with a template (Optional)
                </Label>
                <Select value={selectedTemplateId} onValueChange={handleTemplateSelect}>
                  <SelectTrigger className="h-9 bg-background">
                    <SelectValue placeholder="Select a template..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Custom Task</SelectItem>
                    {(() => {
                      const grouped = templates.reduce((acc, template) => {
                        if (!acc[template.category]) {
                          acc[template.category] = [];
                        }
                        acc[template.category].push(template);
                        return acc;
                      }, {} as Record<string, TaskTemplate[]>);

                      return Object.entries(grouped).map(([category, categoryTemplates]) => (
                        <SelectGroup key={category}>
                          <SelectLabel>{category}</SelectLabel>
                          {categoryTemplates.map((template) => {
                            const IconComponent = getTemplateIcon(template.name);
                            return (
                              <SelectItem key={template.id} value={template.id}>
                                <div className="flex items-center gap-2">
                                  <IconComponent className="h-4 w-4" />
                                  {template.name}
                                </div>
                              </SelectItem>
                            );
                          })}
                        </SelectGroup>
                      ));
                    })()}
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-4">
              {/* Task Name */}
              <div className="space-y-2">
                <Label htmlFor="name" className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider">Monitor Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., iPhone 16 Release Monitor"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (validationErrors.name) setValidationErrors(prev => ({ ...prev, name: "" }));
                  }}
                  disabled={isSubmitting}
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
                  placeholder="e.g., When is the next iPhone being announced by Apple?"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    if (validationErrors.searchQuery) setValidationErrors(prev => ({ ...prev, searchQuery: "" }));
                  }}
                  disabled={isSubmitting}
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
                  placeholder="e.g., A specific release date or month is officially announced"
                  value={conditionDescription}
                  onChange={(e) => {
                    setConditionDescription(e.target.value);
                    if (validationErrors.conditionDescription) setValidationErrors(prev => ({ ...prev, conditionDescription: "" }));
                  }}
                  disabled={isSubmitting}
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

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </form>
        </div>

        <DialogFooter className="pt-4 border-t-2 border-zinc-100 flex-shrink-0 gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={handleCreateTask} disabled={isSubmitting} className="shadow-brutalist">
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create Monitor
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
