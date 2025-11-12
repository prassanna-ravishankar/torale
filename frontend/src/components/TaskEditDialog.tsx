import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { WizardStepQuery } from '@/components/wizard/WizardStepQuery';
import { WizardStepPreview } from '@/components/wizard/WizardStepPreview';
import { WizardStepSchedule } from '@/components/wizard/WizardStepSchedule';
import { WizardNavigation } from '@/components/wizard/WizardNavigation';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { Task } from '@/types';

type WizardStep = 'query' | 'preview' | 'schedule';
type NotifyBehavior = 'once' | 'always' | 'track_state';

interface PreviewResult {
  answer: string;
  condition_met: boolean;
  inferred_condition?: string;
  grounding_sources: Array<{ url: string; title: string }>;
  current_state: any;
}

interface TaskEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task | null;
  onSuccess: (task: Task) => void;
}

export const TaskEditDialog: React.FC<TaskEditDialogProps> = ({
  open,
  onOpenChange,
  task,
  onSuccess,
}) => {
  // Wizard state
  const [currentStep, setCurrentStep] = useState<WizardStep>('query');

  // Form data
  const [name, setName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [conditionDescription, setConditionDescription] = useState('');
  const [schedule, setSchedule] = useState('0 9 * * *');
  const [notifyBehavior, setNotifyBehavior] = useState<NotifyBehavior>('track_state');

  // UI state
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [previewResult, setPreviewResult] = useState<PreviewResult | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string>('');
  const [isUpdating, setIsUpdating] = useState(false);

  // Load task data when task changes
  useEffect(() => {
    if (task && open) {
      setName(task.name);
      setSearchQuery(task.search_query || '');
      setConditionDescription(task.condition_description || '');
      setSchedule(task.schedule);
      setNotifyBehavior(task.notify_behavior as NotifyBehavior);
    }
  }, [task, open]);

  // Reset on close
  useEffect(() => {
    if (!open) {
      setTimeout(() => {
        setCurrentStep('query');
        setValidationErrors({});
        setPreviewResult(null);
        setPreviewError('');
      }, 200);
    }
  }, [open]);

  // Step helpers
  const stepOrder: WizardStep[] = ['query', 'preview', 'schedule'];
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
    if (currentStep === 'query') {
      if (validateQueryStep()) {
        setCurrentStep('preview');
      }
    } else if (currentStep === 'preview') {
      if (validatePreviewStep()) {
        setCurrentStep('schedule');
      }
    } else if (currentStep === 'schedule') {
      await handleUpdate();
    }
  };

  const handleBack = () => {
    if (currentStep === 'preview') {
      setCurrentStep('query');
    } else if (currentStep === 'schedule') {
      setCurrentStep('preview');
    }
  };

  const handleEditQuery = () => {
    setCurrentStep('query');
  };

  // Update task
  const handleUpdate = async () => {
    if (!task) return;

    setIsUpdating(true);

    try {
      // Use inferred condition if user didn't provide one
      const finalCondition = conditionDescription || previewResult?.inferred_condition || '';

      const updatedTask = await api.updateTask(task.id, {
        name,
        search_query: searchQuery,
        condition_description: finalCondition,
        schedule,
        notify_behavior: notifyBehavior,
      });

      toast.success('Task updated successfully');
      onSuccess(updatedTask);
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to update task:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to update task');
    } finally {
      setIsUpdating(false);
    }
  };

  if (!task) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Edit Task</DialogTitle>
          <DialogDescription>
            Update your monitoring task in {totalSteps} steps
          </DialogDescription>
          <div className="pt-4">
            <Progress value={((currentStepIndex + 1) / totalSteps) * 100} />
          </div>
        </DialogHeader>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto min-h-0 px-1">
          {currentStep === 'query' && (
            <WizardStepQuery
              searchQuery={searchQuery}
              onSearchQueryChange={(value) => {
                // Clear condition when query changes to force re-inference
                if (value !== searchQuery) {
                  setConditionDescription('');
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
        </div>

        {/* Footer Navigation */}
        <WizardNavigation
          currentStep={currentStepIndex + 1}
          totalSteps={totalSteps}
          onNext={handleNext}
          onBack={handleBack}
          onCancel={() => onOpenChange(false)}
          nextLabel={currentStep === 'schedule' ? 'Update Task' : undefined}
          isNextDisabled={false}
          isLoading={isUpdating}
          showBack={currentStep !== 'query'}
        />
      </DialogContent>
    </Dialog>
  );
};
