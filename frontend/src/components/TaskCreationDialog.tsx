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
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { NotifyBehavior, TaskTemplate, Task } from "@/types";
import api from "@/lib/api";
import {
  Loader2,
  Sparkles,
  Search,
  Bell,
  Clock,
  AlertCircle,
  Zap,
  Eye,
  RotateCcw,
  Music,
  Waves,
  Gamepad2,
  Code2,
  Bot,
  Cpu,
  Calendar,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from 'sonner';
import { cn } from "@/lib/utils";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { CustomScheduleDialog } from "@/components/ui/CustomScheduleDialog";
import cronstrue from "cronstrue";

interface TaskCreationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated: (task?: Task) => void;
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

const SIMPLE_SCHEDULE_OPTIONS = [
  { value: "*/30 * * * *", label: "Every 30 minutes", icon: Zap },
  { value: "0 */6 * * *", label: "Every 6 hours", icon: Clock },
  { value: "0 9 * * *", label: "Daily at 9:00 AM", icon: Clock },
  { value: "0 12 * * *", label: "Daily at noon", icon: Clock },
  { value: "0 8 * * 1", label: "Weekly on Monday", icon: Clock },
  { value: "custom", label: "Custom Schedule...", icon: Calendar },
];

const NOTIFY_BEHAVIORS = [
  {
    value: "once" as NotifyBehavior,
    label: "Notify Once",
    description: "Stop monitoring after first match",
    icon: Bell,
  },
  {
    value: "always" as NotifyBehavior,
    label: "Always Notify",
    description: "Alert every time condition is met",
    icon: RotateCcw,
  },
  {
    value: "track_state" as NotifyBehavior,
    label: "Track Changes",
    description: "Notify when information changes",
    icon: Eye,
  }
];

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
  const [schedule, setSchedule] = useState("0 9 * * *");
  const [notifyBehavior, setNotifyBehavior] = useState<NotifyBehavior>("track_state");

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Magic Input state
  const [magicPrompt, setMagicPrompt] = useState("");
  const [isMagicLoading, setIsMagicLoading] = useState(false);

  // Custom Schedule Dialog state
  const [isCustomScheduleOpen, setIsCustomScheduleOpen] = useState(false);

  const handleSuggest = async () => {
    if (!magicPrompt.trim()) return;

    setIsMagicLoading(true);
    try {
      const suggestion = await api.suggestTask(magicPrompt);

      setName(suggestion.name);
      setSearchQuery(suggestion.search_query);
      setConditionDescription(suggestion.condition_description);
      setSchedule(suggestion.schedule);
      setNotifyBehavior(suggestion.notify_behavior as NotifyBehavior);

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
  const [showAdvanced, setShowAdvanced] = useState(false);

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
      setSchedule("0 9 * * *");
      setNotifyBehavior("track_state");
      setValidationErrors({});
      setError("");
      setShowAdvanced(false);
      setMagicPrompt(""); // Reset magic prompt
      setIsMagicLoading(false); // Reset magic loading
      setIsCustomScheduleOpen(false);
    }
  }, [open]);

  // Auto-fill form when template is selected
  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);

    if (!templateId || templateId === "none") {
      // Don't clear fields if user just wants to switch back to "custom" to edit
      return;
    }

    const template = templates.find(t => t.id === templateId);
    if (template) {
      setName(template.name);
      setSearchQuery(template.search_query);
      setConditionDescription(template.condition_description);
      setSchedule(template.schedule);
      setNotifyBehavior(template.notify_behavior);
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
        schedule,
        notify_behavior: notifyBehavior,
        executor_type: "llm_grounded_search",
        config: {
          search_provider: "google"
        },
        is_active: true,
        run_immediately: true,
      });

      toast.success('Task created and started! 🚀');
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
      <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-2xl font-bold tracking-tight">
            Create Monitoring Task
          </DialogTitle>
          <DialogDescription>
            Create a new monitoring task. Fill in the details below or use Magic Input.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Magic Input Section */}
          <div className="bg-muted/30 p-4 rounded-lg border border-dashed border-muted-foreground/25 space-y-3">
            <div className="flex items-center gap-2 text-sm font-medium text-primary">
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
              <div className="bg-muted/30 p-3 rounded-lg border border-border/50">
                <Label className="text-xs font-medium text-muted-foreground mb-2 block">
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
                <Label htmlFor="name" className="font-semibold">Task Name</Label>
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
                <Label htmlFor="searchQuery" className="font-semibold flex items-center gap-2">
                  <Search className="h-4 w-4" />
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
                <Label htmlFor="condition" className="font-semibold flex items-center gap-2">
                  <Bell className="h-4 w-4" />
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
            </div>

            {/* Progressive Disclosure: Advanced Options */}
            <Collapsible open={showAdvanced} onOpenChange={setShowAdvanced} className="space-y-2">
              <div className="flex items-center justify-between">
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm" className="p-0 h-auto font-medium text-muted-foreground hover:text-foreground">
                    {showAdvanced ? (
                      <span className="flex items-center gap-1">Hide Advanced Options <ChevronUp className="h-4 w-4" /></span>
                    ) : (
                      <span className="flex items-center gap-1">Show Advanced Options <ChevronDown className="h-4 w-4" /></span>
                    )}
                  </Button>
                </CollapsibleTrigger>
                {!showAdvanced && (
                  <span className="text-xs text-muted-foreground">
                    Daily checks, Track changes
                  </span>
                )}
              </div>

              <CollapsibleContent className="space-y-4 pt-2 animate-in slide-in-from-top-2 fade-in duration-200">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-muted/30 rounded-lg border border-border/50">
                  {/* Schedule */}
                  <div className="space-y-2">
                    <Label htmlFor="schedule" className="text-sm font-medium flex items-center gap-2">
                      <Clock className="h-3.5 w-3.5" />
                      Check Frequency
                    </Label>
                    <div className="space-y-2">
                      <Select
                        value={SIMPLE_SCHEDULE_OPTIONS.some(o => o.value === schedule) ? schedule : "custom"}
                        onValueChange={(val) => {
                          if (val === "custom") {
                            setIsCustomScheduleOpen(true);
                          } else {
                            setSchedule(val);
                          }
                        }}
                        disabled={isSubmitting}
                      >
                        <SelectTrigger id="schedule" className="h-9 bg-background">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {SIMPLE_SCHEDULE_OPTIONS.map((option) => {
                            const IconComponent = option.icon;
                            return (
                              <SelectItem key={option.value} value={option.value}>
                                <div className="flex items-center gap-2">
                                  <IconComponent className="h-3.5 w-3.5" />
                                  {option.label}
                                </div>
                              </SelectItem>
                            );
                          })}
                        </SelectContent>
                      </Select>

                      {/* Custom Schedule Display & Edit */}
                      {(!SIMPLE_SCHEDULE_OPTIONS.some(o => o.value === schedule) || schedule === "custom") && (
                        <div className="animate-in slide-in-from-top-1 fade-in duration-200 flex items-center gap-2">
                          <div className="flex-1 text-xs bg-muted px-3 py-2 rounded-md border font-mono truncate">
                            {schedule === "custom" ? "No schedule selected" : schedule}
                            <span className="ml-2 text-muted-foreground font-sans">
                              ({(() => {
                                try {
                                  return cronstrue.toString(schedule);
                                } catch {
                                  return "Invalid cron";
                                }
                              })()})
                            </span>
                          </div>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => setIsCustomScheduleOpen(true)}
                            className="h-9 px-3"
                          >
                            Edit
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>

                  <CustomScheduleDialog
                    open={isCustomScheduleOpen}
                    onOpenChange={setIsCustomScheduleOpen}
                    initialValue={SIMPLE_SCHEDULE_OPTIONS.some(o => o.value === schedule) ? "0 9 * * *" : schedule}
                    onSave={(newSchedule) => {
                      setSchedule(newSchedule);
                    }}
                  />

                  {/* Notification Behavior */}
                  <div className="space-y-2">
                    <Label htmlFor="notifyBehavior" className="text-sm font-medium flex items-center gap-2">
                      <Bell className="h-3.5 w-3.5" />
                      Notification Mode
                    </Label>
                    <Select
                      value={notifyBehavior}
                      onValueChange={(value) => setNotifyBehavior(value as NotifyBehavior)}
                      disabled={isSubmitting}
                    >
                      <SelectTrigger id="notifyBehavior" className="h-9 bg-background">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {NOTIFY_BEHAVIORS.map((behavior) => (
                          <SelectItem key={behavior.value} value={behavior.value}>
                            {behavior.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CollapsibleContent>
            </Collapsible>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </form>
        </div>

        <DialogFooter className="pt-4 border-t flex-shrink-0">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={handleCreateTask} disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Create Task
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
