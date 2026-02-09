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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CollapsibleSection } from "@/components/torale";
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
  AlertCircle,
  Gamepad2,
  Rocket,
  TrendingDown,
  Eclipse,
  Camera,
  Smartphone,
  TrainFront,
  Briefcase,
  Bot,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from 'sonner';
import { cn } from "@/lib/utils";

interface TaskCreationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated: (task: Task) => void;
}

// Icon mapping for templates by category
const categoryIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  gaming: Gamepad2,
  space: Rocket,
  finance: TrendingDown,
  nature: Eclipse,
  photography: Camera,
  tech: Smartphone,
  travel: TrainFront,
  careers: Briefcase,
};

const getTemplateIcon = (category: string) => {
  return categoryIcons[category.toLowerCase()] ?? Sparkles;
};

const MIN_INSTRUCTIONS_LENGTH = 10;

export const TaskCreationDialog: React.FC<TaskCreationDialogProps> = ({
  open,
  onOpenChange,
  onTaskCreated,
}) => {
  // Form data
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("none");
  const [instructions, setInstructions] = useState("");

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);

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
        toast.error("Failed to load templates. Please check your connection.");
      }
    };
    loadTemplates();
  }, []);

  // Reset state when dialog closes
  useEffect(() => {
    if (!open) {
      setSelectedTemplateId("none");
      setInstructions("");
      setValidationErrors({});
      setError("");
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
      // Concatenate query and condition for the single input if they differ
      if (template.condition_description && template.condition_description !== template.search_query) {
        setInstructions(`${template.search_query}\n\nNotify when: ${template.condition_description}`);
      } else {
        setInstructions(template.search_query);
      }
    }
  };

  // Validation
  const validate = (): boolean => {
    const errors: Record<string, string> = {};

    if (!instructions.trim()) {
      errors.instructions = "Please describe what to monitor";
    } else if (instructions.length < MIN_INSTRUCTIONS_LENGTH) {
      errors.instructions = "Please provide more detail";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Task creation
  const handleCreateTask = async () => {
    if (!validate()) {
      toast.error("Please describe what to monitor");
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      // We rely on the backend/agent to:
      // 1. Infer the name (topic)
      // 2. Infer the condition (from instructions)
      // 3. Determine next_run timing
      const newTask = await api.createTask({
        search_query: instructions,
        condition_description: instructions,
        notify_behavior: "once",
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
            Describe what you want to track. AI will handle the rest.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">

            <div className="space-y-4">
              {/* Instructions */}
              <div className="space-y-2">
                <Label htmlFor="instructions" className="text-[10px] font-mono uppercase text-zinc-400 tracking-wider">
                  What to Monitor
                </Label>
                <Textarea
                  id="instructions"
                  placeholder={"Next iPhone release\n\n💡 Keep it simple — our agent figures out the details"}
                  value={instructions}
                  onChange={(e) => {
                    setInstructions(e.target.value);
                    if (validationErrors.instructions) setValidationErrors(prev => ({ ...prev, instructions: "" }));
                  }}
                  disabled={isSubmitting}
                  rows={6}
                  className={cn("resize-none font-mono text-sm p-3", validationErrors.instructions && "border-destructive")}
                />
                {validationErrors.instructions && (
                  <p className="text-xs text-destructive flex items-center gap-1.5">
                    <AlertCircle className="h-3 w-3" />
                    {validationErrors.instructions}
                  </p>
                )}
              </div>
            </div>

            {/* Template Selection */}
            {templates.length > 0 && (
              <CollapsibleSection
                title="Need inspiration?"
                defaultOpen={false}
                variant="default"
              >
                <div className="p-3">
                  <Select value={selectedTemplateId} onValueChange={handleTemplateSelect}>
                    <SelectTrigger className="h-8 bg-background">
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
                              const IconComponent = getTemplateIcon(template.category);
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
              </CollapsibleSection>
            )}

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
            Start Monitor
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
