import React from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface WizardNavigationProps {
  currentStep: number;
  totalSteps: number;
  onNext: () => void;
  onBack: () => void;
  onCancel: () => void;
  nextLabel?: string;
  backLabel?: string;
  isNextDisabled?: boolean;
  isLoading?: boolean;
  showBack?: boolean;
}

export const WizardNavigation: React.FC<WizardNavigationProps> = ({
  currentStep,
  totalSteps,
  onNext,
  onBack,
  onCancel,
  nextLabel = 'Continue',
  backLabel = 'Back',
  isNextDisabled = false,
  isLoading = false,
  showBack = true,
}) => {
  const isLastStep = currentStep === totalSteps;
  const isFirstStep = currentStep === 1;

  return (
    <div className={cn(
      "flex items-center justify-between pt-4 border-t",
      "sticky sm:relative bottom-0 sm:bottom-auto",
      "bg-background",
      "flex-shrink-0"
    )}>
      {/* Step Indicator */}
      <div className="text-sm text-muted-foreground">
        Step {currentStep} of {totalSteps}
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>

        {showBack && !isFirstStep && (
          <Button
            type="button"
            variant="outline"
            onClick={onBack}
            disabled={isLoading}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            {backLabel}
          </Button>
        )}

        <Button
          type="button"
          onClick={onNext}
          disabled={isNextDisabled || isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Loading...
            </>
          ) : (
            <>
              {isLastStep ? nextLabel : 'Continue'}
              {!isLastStep && <ChevronRight className="h-4 w-4 ml-1" />}
            </>
          )}
        </Button>
      </div>
    </div>
  );
};
