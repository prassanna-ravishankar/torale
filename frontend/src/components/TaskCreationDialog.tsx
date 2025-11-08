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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import type { NotifyBehavior, TaskTemplate } from "@/types";
import api from "@/lib/api";
import {
  Loader2,
  Info,
  Sparkles,
  Search,
  Bell,
  Clock,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  AlertCircle,
  Zap,
  Eye,
  RotateCcw,
  Music,
  Waves,
  Gamepad2,
  Code2,
  Bot,
  Cpu
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from 'sonner';
import { cn } from "@/lib/utils";

interface TaskCreationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated: () => void;
}

type DialogStage = 'select' | 'edit' | 'advanced';

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
];

const ADVANCED_SCHEDULE_OPTIONS = [
  { value: "*/30 * * * *", label: "Every 30 minutes", icon: Zap, description: "High frequency", nextCheck: "in 30 minutes" },
  { value: "0 */6 * * *", label: "Every 6 hours", icon: Clock, description: "Regular checks", nextCheck: "in 6 hours" },
  { value: "0 9 * * *", label: "Daily at 9:00 AM", icon: Clock, description: "Morning updates", nextCheck: "tomorrow at 9:00 AM" },
  { value: "0 12 * * *", label: "Daily at noon", icon: Clock, description: "Midday checks", nextCheck: "tomorrow at noon" },
  { value: "0 8 * * 1", label: "Weekly on Monday", icon: Clock, description: "Weekly summary", nextCheck: "next Monday at 8:00 AM" },
  { value: "0 0 * * 0", label: "Weekly on Sunday", icon: Clock, description: "Weekly review", nextCheck: "next Sunday at midnight" },
];

const NOTIFY_BEHAVIORS = [
  {
    value: "once" as NotifyBehavior,
    label: "Notify Once",
    description: "Stop monitoring after first match",
    icon: Bell,
    example: "Perfect for one-time events like product releases"
  },
  {
    value: "always" as NotifyBehavior,
    label: "Always Notify",
    description: "Alert every time condition is met",
    icon: RotateCcw,
    example: "Best for recurring updates like daily stock prices"
  },
  {
    value: "track_state" as NotifyBehavior,
    label: "Track Changes",
    description: "Notify when information changes",
    icon: Eye,
    example: "Ideal for monitoring evolving situations"
  }
];

const EXAMPLE_QUERIES = [
  { query: "When is the next iPhone being released?", condition: "A specific release date is announced" },
  { query: "Is PlayStation 5 in stock at Best Buy?", condition: "The console is available for purchase" },
];

const MIN_NAME_LENGTH = 3;
const MIN_SEARCH_QUERY_LENGTH = 10;
const MIN_CONDITION_DESCRIPTION_LENGTH = 10;

export const TaskCreationDialog: React.FC<TaskCreationDialogProps> = ({
  open,
  onOpenChange,
  onTaskCreated,
}) => {
  // Stage management
  const [stage, setStage] = useState<DialogStage>('select');
  const [wizardStep, setWizardStep] = useState(1);

  // Form data
  const [templates, setTemplates] = useState<TaskTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("none");
  const [name, setName] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [conditionDescription, setConditionDescription] = useState("");
  const [schedule, setSchedule] = useState("0 9 * * *");
  const [notifyBehavior, setNotifyBehavior] = useState<NotifyBehavior>("track_state");

  // UI state
  const [isLoading, setIsLoading] = useState(false);
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
      setStage('select');
      setWizardStep(1);
      setSelectedTemplateId("none");
      setName("");
      setSearchQuery("");
      setConditionDescription("");
      setSchedule("0 9 * * *");
      setNotifyBehavior("track_state");
      setValidationErrors({});
      setError("");
    }
  }, [open]);

  // Auto-fill form when template is selected
  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);

    if (!templateId || templateId === "none") {
      // Create from scratch - set defaults and go to edit
      setName("");
      setSearchQuery("");
      setConditionDescription("");
      setSchedule("0 9 * * *");
      setNotifyBehavior("track_state");
      setStage('edit');
      return;
    }

    const template = templates.find(t => t.id === templateId);
    if (template) {
      setName(template.name);
      setSearchQuery(template.search_query);
      setConditionDescription(template.condition_description);
      setSchedule(template.schedule);
      setNotifyBehavior(template.notify_behavior);
      // Auto-advance to edit stage
      setStage('edit');
    }
  };

  // Validation
  const validateSimpleMode = (): boolean => {
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

  const validateAdvancedStep1 = (): boolean => {
    return validateSimpleMode();
  };

  // Navigation handlers
  const handleBackToSelect = () => {
    setStage('select');
    setValidationErrors({});
  };

  const handleGoToAdvanced = () => {
    if (!validateSimpleMode()) {
      toast.error("Please fix the errors before continuing");
      return;
    }
    setStage('advanced');
    setWizardStep(1);
  };

  const handleBackFromAdvanced = () => {
    setStage('edit');
    setWizardStep(1);
  };

  const handleAdvancedNextStep = () => {
    if (wizardStep === 1 && !validateAdvancedStep1()) {
      return;
    }
    setWizardStep(prev => Math.min(prev + 1, 3));
  };

  const handleAdvancedPrevStep = () => {
    if (wizardStep === 1) {
      handleBackFromAdvanced();
    } else {
      setWizardStep(prev => Math.max(prev - 1, 1));
    }
  };

  const getNextCheckTime = (cronExpression: string): string => {
    const option = ADVANCED_SCHEDULE_OPTIONS.find(opt => opt.value === cronExpression);
    return option?.nextCheck || "based on your schedule";
  };

  // Task creation
  const handleCreateTask = async () => {
    // Validate before creating
    if (!validateSimpleMode()) {
      toast.error("Please fix the errors before creating");
      return;
    }

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
        config: {
          search_provider: "google"
        },
        is_active: true,
      });

      toast.success('Task created successfully');
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (stage === 'advanced' && wizardStep < 3) {
      handleAdvancedNextStep();
    } else {
      handleCreateTask();
    }
  };

  const progressPercentage = stage === 'advanced' ? (wizardStep / 3) * 100 : 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={cn(
        "overflow-hidden flex flex-col",
        stage === 'select' && "max-w-5xl",
        stage === 'edit' && "max-w-4xl max-h-[85vh]",
        stage === 'advanced' && "max-w-3xl max-h-[85vh]"
      )}>
        <DialogHeader className="space-y-2 pb-4 flex-shrink-0">
          <DialogTitle className={cn(
            "text-2xl font-bold tracking-tight",
            (stage === 'select' || stage === 'advanced') && "flex items-center gap-2"
          )}>
            {stage === 'select' && <><Sparkles className="h-6 w-6 text-purple-500" />Choose a Template</>}
            {stage === 'edit' && "Configure Your Task"}
            {stage === 'advanced' && <><Sparkles className="h-6 w-6 text-purple-500" />Advanced Settings</>}
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            {stage === 'select' && "Start with a pre-built template or create from scratch"}
            {stage === 'edit' && "Review and customize your monitoring task"}
            {stage === 'advanced' && "Fine-tune every aspect of your monitoring task"}
          </DialogDescription>
        </DialogHeader>

        {/* Progress Bar (Advanced Mode Only) */}
        {stage === 'advanced' && (
          <div className="space-y-3 pb-4 border-b flex-shrink-0">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground font-medium">Step {wizardStep} of 3</span>
              <span className="text-muted-foreground">{Math.round(progressPercentage)}%</span>
            </div>
            <Progress value={progressPercentage} className="h-1.5" />
            <div className="flex items-center justify-between">
              <div className={cn(
                "flex items-center gap-1.5 text-xs transition-colors",
                wizardStep >= 1 ? "text-primary font-medium" : "text-muted-foreground"
              )}>
                <Search className="h-3.5 w-3.5" />
                <span>What</span>
              </div>
              <div className={cn(
                "flex items-center gap-1.5 text-xs transition-colors",
                wizardStep >= 2 ? "text-primary font-medium" : "text-muted-foreground"
              )}>
                <Clock className="h-3.5 w-3.5" />
                <span>When</span>
              </div>
              <div className={cn(
                "flex items-center gap-1.5 text-xs transition-colors",
                wizardStep >= 3 ? "text-primary font-medium" : "text-muted-foreground"
              )}>
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Review</span>
              </div>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto min-h-0">
          <form onSubmit={handleSubmit} className="space-y-6 p-1">
            {/* STAGE 1: TEMPLATE SELECTION */}
            {stage === 'select' && (
              <div className="space-y-4">
                {/* Template Cards Grid */}
                {templates.length > 0 && (
                  <div className="grid grid-cols-3 gap-3">
                    {templates.map((template) => {
                      const IconComponent = getTemplateIcon(template.name);
                      return (
                        <Card
                          key={template.id}
                          className="cursor-pointer transition-all duration-200 hover:border-primary hover:shadow-sm group relative overflow-hidden"
                          onClick={() => handleTemplateSelect(template.id)}
                        >
                          <div className="absolute inset-0 bg-gradient-to-br from-primary/3 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                          <CardHeader className="p-3 relative">
                            <div className="flex items-center gap-2.5">
                              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/15 transition-colors">
                                <IconComponent className="h-4 w-4 text-primary" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <CardTitle className="text-sm font-semibold group-hover:text-primary transition-colors leading-tight mb-0.5">
                                  {template.name}
                                </CardTitle>
                                <CardDescription className="text-[10px] leading-snug text-muted-foreground/70 line-clamp-2">
                                  {template.description}
                                </CardDescription>
                              </div>
                            </div>
                          </CardHeader>
                        </Card>
                      );
                    })}
                  </div>
                )}

                {/* Create from Scratch Option */}
                <div className="flex items-center gap-3">
                  <Separator className="flex-1" />
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => handleTemplateSelect("none")}
                    className="gap-2 text-muted-foreground hover:text-primary"
                  >
                    <Sparkles className="h-4 w-4" />
                    <span className="text-sm">Or start from scratch</span>
                  </Button>
                  <Separator className="flex-1" />
                </div>
              </div>
            )}

            {/* STAGE 2: EDIT/REVIEW */}
            {stage === 'edit' && (
              <div className="space-y-6">
                {/* Task Name - Full Width */}
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-base font-semibold">Task Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., iPhone 16 Release Monitor"
                    value={name}
                    onChange={(e) => {
                      setName(e.target.value);
                      if (validationErrors.name) {
                        setValidationErrors(prev => ({ ...prev, name: "" }));
                      }
                    }}
                    disabled={isLoading}
                    className={cn("h-11 text-base", validationErrors.name && "border-destructive")}
                  />
                  {validationErrors.name && (
                    <p className="text-xs text-destructive flex items-center gap-1.5">
                      <AlertCircle className="h-3 w-3" />
                      {validationErrors.name}
                    </p>
                  )}
                </div>

                {/* Search Query - Full Width */}
                <div className="space-y-2">
                  <Label htmlFor="searchQuery" className="text-base font-semibold flex items-center gap-2">
                    <Search className="h-4 w-4" />
                    What to Monitor
                  </Label>
                  <Textarea
                    id="searchQuery"
                    placeholder="e.g., When is the next iPhone being announced by Apple?"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      if (validationErrors.searchQuery) {
                        setValidationErrors(prev => ({ ...prev, searchQuery: "" }));
                      }
                    }}
                    disabled={isLoading}
                    rows={3}
                    className={cn("text-base resize-none leading-relaxed", validationErrors.searchQuery && "border-destructive")}
                  />
                  {validationErrors.searchQuery && (
                    <p className="text-xs text-destructive flex items-center gap-1.5">
                      <AlertCircle className="h-3 w-3" />
                      {validationErrors.searchQuery}
                    </p>
                  )}
                </div>

                {/* Condition Description - Full Width */}
                <div className="space-y-2">
                  <Label htmlFor="condition" className="text-base font-semibold flex items-center gap-2">
                    <Bell className="h-4 w-4" />
                    When to Notify
                  </Label>
                  <Textarea
                    id="condition"
                    placeholder="e.g., A specific release date or month is officially announced"
                    value={conditionDescription}
                    onChange={(e) => {
                      setConditionDescription(e.target.value);
                      if (validationErrors.conditionDescription) {
                        setValidationErrors(prev => ({ ...prev, conditionDescription: "" }));
                      }
                    }}
                    disabled={isLoading}
                    rows={3}
                    className={cn("text-base resize-none leading-relaxed", validationErrors.conditionDescription && "border-destructive")}
                  />
                  {validationErrors.conditionDescription && (
                    <p className="text-xs text-destructive flex items-center gap-1.5">
                      <AlertCircle className="h-3 w-3" />
                      {validationErrors.conditionDescription}
                    </p>
                  )}
                </div>

                {/* Schedule & Notification - Two Columns */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Schedule - Left Column */}
                  <div className="space-y-2">
                    <Label htmlFor="schedule" className="text-base font-semibold flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Check Frequency
                    </Label>
                    <Select value={schedule} onValueChange={setSchedule} disabled={isLoading}>
                      <SelectTrigger id="schedule" className="h-11 text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {SIMPLE_SCHEDULE_OPTIONS.map((option) => {
                          const IconComponent = option.icon;
                          return (
                            <SelectItem key={option.value} value={option.value} className="text-sm">
                              <div className="flex items-center gap-2">
                                <IconComponent className="h-4 w-4" />
                                {option.label}
                              </div>
                            </SelectItem>
                          );
                        })}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Notification Behavior - Right Column */}
                  <div className="space-y-2">
                    <Label htmlFor="notifyBehavior" className="text-base font-semibold flex items-center gap-2">
                      <Bell className="h-4 w-4" />
                      Notification Mode
                    </Label>
                    <Select
                      value={notifyBehavior}
                      onValueChange={(value) => setNotifyBehavior(value as NotifyBehavior)}
                      disabled={isLoading}
                    >
                      <SelectTrigger id="notifyBehavior" className="h-11 text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {NOTIFY_BEHAVIORS.map((behavior) => (
                          <SelectItem key={behavior.value} value={behavior.value} className="text-sm">
                            {behavior.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Info Alert - Full Width */}
                <Alert className="border-primary/20 bg-primary/5">
                  <Info className="h-4 w-4 text-primary" />
                  <AlertDescription className="text-sm leading-relaxed">
                    The AI will search the web, analyze results, and notify you when your condition is met.
                    {' '}<button
                      type="button"
                      onClick={handleGoToAdvanced}
                      className="underline font-semibold hover:text-primary transition-colors"
                    >
                      Need advanced settings?
                    </button>
                  </AlertDescription>
                </Alert>
              </div>
            )}

            {/* STAGE 3: ADVANCED WIZARD */}
            {stage === 'advanced' && wizardStep === 1 && (
              <div className="space-y-6">
              {/* Template Selection */}
              {templates.length > 0 && (
                <Card className="border-dashed">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Sparkles className="h-4 w-4 text-purple-500" />
                      Quick Start with Template
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Select value={selectedTemplateId} onValueChange={handleTemplateSelect}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a template or create from scratch..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Create from scratch</SelectItem>
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
                  </CardContent>
                </Card>
              )}

              {/* Task Name */}
              <div className="space-y-3">
                <Label htmlFor="name-adv" className="text-base font-semibold flex items-center gap-2">
                  Task Name
                  <Badge variant="secondary" className="text-xs">Required</Badge>
                </Label>
                <Input
                  id="name-adv"
                  placeholder="e.g., iPhone 16 Release Monitor"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (validationErrors.name) {
                      setValidationErrors(prev => ({ ...prev, name: "" }));
                    }
                  }}
                  disabled={isLoading}
                  className={cn(
                    "text-base h-12",
                    validationErrors.name && "border-destructive"
                  )}
                />
                {validationErrors.name ? (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {validationErrors.name}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Give your monitoring task a memorable name
                  </p>
                )}
              </div>

              {/* Search Query */}
              <div className="space-y-3">
                <Label htmlFor="searchQuery-adv" className="text-base font-semibold flex items-center gap-2">
                  <Search className="h-4 w-4" />
                  Search Query
                  <Badge variant="secondary" className="text-xs">Required</Badge>
                </Label>
                <Textarea
                  id="searchQuery-adv"
                  placeholder="e.g., When is the next iPhone being announced by Apple?"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    if (validationErrors.searchQuery) {
                      setValidationErrors(prev => ({ ...prev, searchQuery: "" }));
                    }
                  }}
                  disabled={isLoading}
                  rows={3}
                  className={cn(
                    "text-base resize-none",
                    validationErrors.searchQuery && "border-destructive"
                  )}
                />
                {validationErrors.searchQuery ? (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {validationErrors.searchQuery}
                  </p>
                ) : (
                  <>
                    <p className="text-sm text-muted-foreground">
                      Ask a specific question in natural language. The AI will search the web for answers.
                    </p>
                    <div className="text-xs text-muted-foreground">
                      {searchQuery.length} characters
                    </div>
                  </>
                )}

                {/* Example Queries */}
                {searchQuery.length === 0 && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Example queries:</p>
                    <div className="flex flex-wrap gap-2">
                      {EXAMPLE_QUERIES.map((example) => (
                        <Button
                          key={example.query}
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSearchQuery(example.query);
                            setConditionDescription(example.condition);
                          }}
                          className="text-xs h-auto py-2"
                        >
                          {example.query}
                        </Button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Condition Description */}
              <div className="space-y-3">
                <Label htmlFor="condition-adv" className="text-base font-semibold flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  Trigger Condition
                  <Badge variant="secondary" className="text-xs">Required</Badge>
                </Label>
                <Textarea
                  id="condition-adv"
                  placeholder="e.g., A specific release date or month is officially announced"
                  value={conditionDescription}
                  onChange={(e) => {
                    setConditionDescription(e.target.value);
                    if (validationErrors.conditionDescription) {
                      setValidationErrors(prev => ({ ...prev, conditionDescription: "" }));
                    }
                  }}
                  disabled={isLoading}
                  rows={2}
                  className={cn(
                    "text-base resize-none",
                    validationErrors.conditionDescription && "border-destructive"
                  )}
                />
                {validationErrors.conditionDescription ? (
                  <p className="text-sm text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {validationErrors.conditionDescription}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Describe when you want to be notified. Be specific about what counts as a match.
                  </p>
                )}
              </div>
            </div>
          )}

            {/* ADVANCED WIZARD - STEP 2: When & How to Notify */}
            {stage === 'advanced' && wizardStep === 2 && (
              <div className="space-y-6">
              {/* Check Frequency */}
              <div className="space-y-3">
                <Label htmlFor="schedule-adv" className="text-base font-semibold flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Check Frequency
                </Label>
                <Select value={schedule} onValueChange={setSchedule} disabled={isLoading}>
                  <SelectTrigger id="schedule-adv" className="h-12">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ADVANCED_SCHEDULE_OPTIONS.map((option) => {
                      const Icon = option.icon;
                      return (
                        <SelectItem key={option.value} value={option.value} className="py-3">
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4" />
                            <div className="flex flex-col">
                              <span className="font-medium">{option.label}</span>
                              <span className="text-xs text-muted-foreground">{option.description}</span>
                            </div>
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    Next check will run <strong>{getNextCheckTime(schedule)}</strong>
                  </AlertDescription>
                </Alert>
              </div>

              {/* Notification Behavior */}
              <div className="space-y-3">
                <Label className="text-base font-semibold flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  Notification Behavior
                </Label>
                <RadioGroup
                  value={notifyBehavior}
                  onValueChange={(value) => setNotifyBehavior(value as NotifyBehavior)}
                  className="space-y-3"
                >
                  {NOTIFY_BEHAVIORS.map((behavior) => {
                    const Icon = behavior.icon;
                    return (
                      <Card
                        key={behavior.value}
                        className={cn(
                          "cursor-pointer transition-all hover:border-primary",
                          notifyBehavior === behavior.value && "border-primary bg-primary/5"
                        )}
                        onClick={() => setNotifyBehavior(behavior.value)}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-start gap-3">
                            <RadioGroupItem value={behavior.value} id={behavior.value} />
                            <div className="flex-1 space-y-1">
                              <div className="flex items-center gap-2">
                                <Icon className="h-4 w-4" />
                                <Label
                                  htmlFor={behavior.value}
                                  className="text-base font-semibold cursor-pointer"
                                >
                                  {behavior.label}
                                </Label>
                              </div>
                              <CardDescription className="text-sm">
                                {behavior.description}
                              </CardDescription>
                              <p className="text-xs text-muted-foreground italic">
                                {behavior.example}
                              </p>
                            </div>
                          </div>
                        </CardHeader>
                      </Card>
                    );
                  })}
                </RadioGroup>
              </div>
            </div>
          )}

            {/* ADVANCED WIZARD - STEP 3: Review & Create */}
            {stage === 'advanced' && wizardStep === 3 && (
              <div className="space-y-6">
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  Review your monitoring task before creating it
                </AlertDescription>
              </Alert>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Task Summary</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="text-sm text-muted-foreground">Task Name</Label>
                    <p className="text-base font-medium mt-1">{name}</p>
                  </div>

                  <Separator />

                  <div>
                    <Label className="text-sm text-muted-foreground flex items-center gap-2">
                      <Search className="h-3 w-3" />
                      Search Query
                    </Label>
                    <p className="text-base mt-1 bg-muted/50 p-3 rounded-md">{searchQuery}</p>
                  </div>

                  <div>
                    <Label className="text-sm text-muted-foreground flex items-center gap-2">
                      <Bell className="h-3 w-3" />
                      Trigger Condition
                    </Label>
                    <p className="text-base mt-1 bg-muted/50 p-3 rounded-md">{conditionDescription}</p>
                  </div>

                  <Separator />

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-sm text-muted-foreground flex items-center gap-2">
                        <Clock className="h-3 w-3" />
                        Frequency
                      </Label>
                      <p className="text-sm mt-1">
                        {ADVANCED_SCHEDULE_OPTIONS.find(opt => opt.value === schedule)?.label}
                      </p>
                    </div>
                    <div>
                      <Label className="text-sm text-muted-foreground">Notifications</Label>
                      <p className="text-sm mt-1">
                        {NOTIFY_BEHAVIORS.find(b => b.value === notifyBehavior)?.label}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription className="text-sm">
                  The AI will search the web using Google, analyze results with Gemini, and notify you when your
                  condition is met. All findings include source links for verification.
                </AlertDescription>
              </Alert>
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </form>
        </div>

        {/* NAVIGATION FOOTER */}
        <DialogFooter className="flex-shrink-0 pt-4 border-t gap-2 sm:gap-3">
          {/* Back Button */}
          {(stage === 'edit' || stage === 'advanced') && (
            <Button
              type="button"
              variant="outline"
              onClick={stage === 'edit' ? handleBackToSelect : handleAdvancedPrevStep}
              disabled={isLoading}
              className="h-10 text-sm"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
          )}

          {/* Cancel Button */}
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isLoading}
            className="h-10 text-sm"
          >
            Cancel
          </Button>

          {/* Action Buttons for Edit Stage */}
          {stage === 'edit' && (
            <Button
              type="button"
              onClick={handleCreateTask}
              disabled={isLoading}
              className="h-10 text-sm px-6 ml-auto"
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Create Task
            </Button>
          )}

          {/* Action Buttons for Advanced Wizard */}
          {stage === 'advanced' && wizardStep < 3 && (
            <Button
              type="button"
              onClick={handleAdvancedNextStep}
              disabled={isLoading}
              className="h-10 text-sm px-6 ml-auto"
            >
              Continue
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          )}

          {stage === 'advanced' && wizardStep === 3 && (
            <Button
              type="submit"
              onClick={handleCreateTask}
              disabled={isLoading}
              className="h-10 text-sm px-6 ml-auto"
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Create Task
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
