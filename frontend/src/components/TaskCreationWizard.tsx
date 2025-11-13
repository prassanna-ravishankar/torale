import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { WizardStepTemplate } from '@/components/wizard/WizardStepTemplate';
import { WizardStepQuery } from '@/components/wizard/WizardStepQuery';
import { WizardStepPreview } from '@/components/wizard/WizardStepPreview';
import { WizardStepSchedule } from '@/components/wizard/WizardStepSchedule';
import { WizardStepHowNotify } from '@/components/wizard/WizardStepHowNotify';
import { WizardNavigation } from '@/components/wizard/WizardNavigation';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { Task, TaskCreatePayload, TaskTemplate, NotificationConfig } from '@/types';

type WizardStep = 'template' | 'query' | 'preview' | 'schedule' | 'howNotify';
type NotifyBehavior = 'once' | 'always' | 'track_state';

interface PreviewResult {
  answer: string;
  condition_met: boolean;
  inferred_condition?: string;
  grounding_sources: Array<{ url: string; title: string }>;
  current_state: any;
}

interface TaskCreationWizardProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: (task: Task) => void;
  selectedTemplate?: TaskTemplate | null;
}

export const TaskCreationWizard: React.FC<TaskCreationWizardProps> = ({
  open,
  onOpenChange,
  onSuccess,
  selectedTemplate: initialTemplate,
}) => {
  // Wizard state
  const [currentStep, setCurrentStep] = useState<WizardStep>('template');
  const [selectedTemplate, setSelectedTemplate] = useState<TaskTemplate | null>(null);

  // Form data
  const [name, setName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [conditionDescription, setConditionDescription] = useState('');
  const [schedule, setSchedule] = useState('0 9 * * *'); // Default: daily at 9am
  const [notifyBehavior, setNotifyBehavior] = useState<NotifyBehavior>('track_state');
  const [notifications, setNotifications] = useState<NotificationConfig[]>([
    { type: 'email' }, // Default to email notifications
  ]);

  // UI state
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [previewResult, setPreviewResult] = useState<PreviewResult | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string>('');
  const [isCreating, setIsCreating] = useState(false);

  // Initialize from initial template if provided
  React.useEffect(() => {
    if (initialTemplate && open) {
      setSelectedTemplate(initialTemplate);
      setName(initialTemplate.name);
      setSearchQuery(initialTemplate.search_query);
      setConditionDescription(initialTemplate.condition_description);
      setSchedule(initialTemplate.schedule);
      setNotifyBehavior(initialTemplate.notify_behavior as NotifyBehavior);
      setCurrentStep('query'); // Skip template step if template provided
    }
  }, [initialTemplate, open]);

  // Reset on close
  React.useEffect(() => {
    if (!open) {
      // Reset after animation completes
      setTimeout(() => {
        setCurrentStep('template');
        setSelectedTemplate(null);
        setName('');
        setSearchQuery('');
        setConditionDescription('');
        setSchedule('0 9 * * *');
        setNotifyBehavior('track_state');
        setNotifications([{ type: 'email' }]);
        setValidationErrors({});
        setPreviewResult(null);
        setPreviewError('');
      }, 200);
    }
  }, [open]);

  // Step helpers
  const stepOrder: WizardStep[] = ['template', 'query', 'preview', 'schedule', 'howNotify'];
  const currentStepIndex = stepOrder.indexOf(currentStep);
  const totalSteps = stepOrder.length;

  // Validation
  const validateQueryStep = (): boolean => {
    const errors: Record<string, string> = {};

    if (!name.trim()) {
      errors.name = 'Task name is required';
    }

    if (!searchQuery.trim()) {
      errors.searchQuery = 'Search query is required';
    } else if (searchQuery.trim().length < 10) {
      errors.searchQuery = 'Search query should be at least 10 characters';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validatePreviewStep = (): boolean => {
    if (!previewResult) {
      toast.error('Please preview your search results before continuing');
      return false;
    }
    return true;
  };

  // Template selection handler
  const handleTemplateSelect = (template: TaskTemplate | null) => {
    setSelectedTemplate(template);

    if (template) {
      // Pre-fill form from template
      setName(template.name);
      setSearchQuery(template.search_query);
      setConditionDescription(template.condition_description);
      setSchedule(template.schedule);
      setNotifyBehavior(template.notify_behavior as NotifyBehavior);
    } else {
      // Start from scratch - use defaults
      setName('');
      setSearchQuery('');
      setConditionDescription('');
      setSchedule('0 9 * * *');
      setNotifyBehavior('track_state');
    }

    // Advance to query step
    setCurrentStep('query');
  };

  const handleChangeTemplate = () => {
    setCurrentStep('template');
  };

  // Preview handler
  const handlePreview = async () => {
    setIsPreviewLoading(true);
    setPreviewError('');

    try {
      const result = await api.previewSearch(
        searchQuery,
        conditionDescription || undefined
      );

      setPreviewResult(result);
      toast.success('Preview loaded successfully');
    } catch (error) {
      console.error('Preview failed:', error);
      const message = error instanceof Error ? error.message : 'Failed to preview search';
      setPreviewError(message);
      toast.error(message);
    } finally {
      setIsPreviewLoading(false);
    }
  };

  // Navigation handlers
  const handleNext = async () => {
    if (currentStep === 'template') {
      // Template step advances via handleTemplateSelect
      return;
    } else if (currentStep === 'query') {
      if (validateQueryStep()) {
        setCurrentStep('preview');
      }
    } else if (currentStep === 'preview') {
      if (validatePreviewStep()) {
        setCurrentStep('schedule');
      }
    } else if (currentStep === 'schedule') {
      setCurrentStep('howNotify');
    } else if (currentStep === 'howNotify') {
      await handleCreate();
    }
  };

  const handleBack = () => {
    if (currentStep === 'query') {
      setCurrentStep('template');
    } else if (currentStep === 'preview') {
      setCurrentStep('query');
    } else if (currentStep === 'schedule') {
      setCurrentStep('preview');
    } else if (currentStep === 'howNotify') {
      setCurrentStep('schedule');
    }
  };

  const handleEditQuery = () => {
    setCurrentStep('query');
  };

  // Create task
  const handleCreate = async () => {
    setIsCreating(true);

    try {
      // Use inferred condition if user didn't provide one
      const finalCondition = conditionDescription || previewResult?.inferred_condition || '';

      const taskPayload: TaskCreatePayload = {
        name,
        search_query: searchQuery,
        condition_description: finalCondition,
        schedule,
        notify_behavior: notifyBehavior,
        executor_type: 'llm_grounded_search',
        config: {
          model: 'gemini-2.0-flash-exp',
        },
        is_active: true,
        run_immediately: true, // Execute immediately
        notifications,
      };

      const task = await api.createTask(taskPayload);

      toast.success('Task created! Running first check...');
      onSuccess(task);
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to create task:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to create task');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Create Monitoring Task</DialogTitle>
          <DialogDescription>
            {currentStep === 'template'
              ? 'Choose a template or start from scratch'
              : `Set up automated monitoring in ${totalSteps} steps`}
          </DialogDescription>
          {currentStep !== 'template' && (
            <div className="pt-4">
              <Progress value={((currentStepIndex + 1) / totalSteps) * 100} />
            </div>
          )}
        </DialogHeader>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto min-h-0 px-1">
          {currentStep === 'template' && (
            <WizardStepTemplate
              onTemplateSelect={handleTemplateSelect}
              selectedTemplate={selectedTemplate}
            />
          )}

          {currentStep === 'query' && (
            <WizardStepQuery
              searchQuery={searchQuery}
              onSearchQueryChange={(value) => {
                // Clear condition and preview results when query changes to prevent stale data
                if (value !== searchQuery) {
                  setConditionDescription('');
                  setPreviewResult(null);
                }
                setSearchQuery(value);
                if (validationErrors.searchQuery) {
                  setValidationErrors((prev) => ({ ...prev, searchQuery: '' }));
                }
              }}
              name={name}
              onNameChange={(value) => {
                setName(value);
                if (validationErrors.name) {
                  setValidationErrors((prev) => ({ ...prev, name: '' }));
                }
              }}
              errors={validationErrors}
              selectedTemplate={selectedTemplate}
              onChangeTemplate={handleChangeTemplate}
            />
          )}

          {currentStep === 'preview' && (
            <WizardStepPreview
              searchQuery={searchQuery}
              conditionDescription={conditionDescription}
              onConditionDescriptionChange={setConditionDescription}
              previewResult={previewResult}
              isLoading={isPreviewLoading}
              onPreview={handlePreview}
              onEditQuery={handleEditQuery}
              error={previewError}
            />
          )}

          {currentStep === 'schedule' && (
            <WizardStepSchedule
              schedule={schedule}
              onScheduleChange={setSchedule}
              notifyBehavior={notifyBehavior}
              onNotifyBehaviorChange={setNotifyBehavior}
            />
          )}

          {currentStep === 'howNotify' && (
            <WizardStepHowNotify
              notifications={notifications}
              onNotificationsChange={setNotifications}
            />
          )}
        </div>

        {/* Footer Navigation - Hidden on template step */}
        {currentStep !== 'template' && (
          <WizardNavigation
            currentStep={currentStepIndex + 1}
            totalSteps={totalSteps}
            onNext={handleNext}
            onBack={handleBack}
            onCancel={() => onOpenChange(false)}
            nextLabel={currentStep === 'howNotify' ? 'Create Task' : undefined}
            isNextDisabled={false}
            isLoading={isCreating}
            showBack={true}
          />
        )}
      </DialogContent>
    </Dialog>
  );
};
