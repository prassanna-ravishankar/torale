import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { SearchPreview } from '@/components/SearchPreview';
import { Loader2, Sparkles, ChevronDown, ChevronUp, AlertCircle, RefreshCw } from 'lucide-react';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { cn } from '@/lib/utils';

interface PreviewResult {
  answer: string;
  condition_met: boolean;
  inferred_condition?: string;
  grounding_sources: Array<{ url: string; title: string }>;
  current_state: any;
}

interface WizardStepPreviewProps {
  searchQuery: string;
  conditionDescription: string;
  onConditionDescriptionChange: (value: string) => void;
  previewResult: PreviewResult | null;
  isLoading: boolean;
  onPreview: () => void;
  onEditQuery: () => void;
  error?: string;
}

export const WizardStepPreview: React.FC<WizardStepPreviewProps> = ({
  searchQuery,
  conditionDescription,
  onConditionDescriptionChange,
  previewResult,
  isLoading,
  onPreview,
  onEditQuery,
  error,
}) => {
  const [isConditionOpen, setIsConditionOpen] = useState(false);

  // Show inferred condition if we have preview results
  const displayCondition = previewResult?.inferred_condition || conditionDescription;
  const isInferred = !!previewResult?.inferred_condition && !conditionDescription;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">Preview Results</h2>
        <p className="text-muted-foreground">
          See what your monitoring task will find. Refine if needed.
        </p>
      </div>

      {/* Query Display */}
      <div className="p-4 bg-muted/50 rounded-lg">
        <p className="text-sm font-medium mb-2">Your Search Query:</p>
        <p className="text-sm text-foreground mb-3">"{searchQuery}"</p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onEditQuery}
          disabled={isLoading}
        >
          <RefreshCw className="h-3 w-3 mr-2" />
          Edit Query
        </Button>
      </div>

      {/* Preview Button / Results */}
      {!previewResult && !isLoading && !error && (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <Sparkles className="h-12 w-12 text-muted-foreground" />
          <div className="text-center space-y-2">
            <h3 className="font-medium">Ready to preview</h3>
            <p className="text-sm text-muted-foreground max-w-md">
              Click below to see what results your search will find
            </p>
          </div>
          <Button onClick={onPreview} size="lg">
            <Sparkles className="h-4 w-4 mr-2" />
            Preview Results
          </Button>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <div className="text-center space-y-2">
            <h3 className="font-medium">Searching...</h3>
            <p className="text-sm text-muted-foreground">
              This may take a few seconds
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-lg space-y-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-destructive">Preview Failed</p>
              <p className="text-sm text-destructive/80 mt-1">{error}</p>
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onPreview}
          >
            <RefreshCw className="h-3 w-3 mr-2" />
            Try Again
          </Button>
        </div>
      )}

      {/* Preview Results */}
      {previewResult && !isLoading && (
        <div className="space-y-4">
          {/* Inferred/Custom Condition Display */}
          {displayCondition && (
            <div className="p-3 bg-muted/50 rounded-lg">
              <div className="flex items-start gap-2">
                <Sparkles className={cn(
                  "h-4 w-4 shrink-0 mt-0.5",
                  isInferred ? "text-primary" : "text-muted-foreground"
                )} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium mb-1">
                    {isInferred ? "We'll notify you when:" : "Notification Condition:"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {displayCondition}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Results Display */}
          <SearchPreview
            answer={previewResult.answer}
            conditionMet={previewResult.condition_met}
            conditionDescription={displayCondition}
            groundingSources={previewResult.grounding_sources}
            currentState={previewResult.current_state}
            showConditionBadge={true}
          />

          {/* Refine Condition (Collapsible) */}
          <Collapsible open={isConditionOpen} onOpenChange={setIsConditionOpen}>
            <CollapsibleTrigger asChild>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="w-full"
              >
                {isConditionOpen ? (
                  <>
                    <ChevronUp className="h-4 w-4 mr-2" />
                    Hide Custom Condition
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 mr-2" />
                    Customize Notification Condition
                  </>
                )}
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent className="pt-4 space-y-2">
              <Label htmlFor="condition-description">
                When should we notify you?
              </Label>
              <Textarea
                id="condition-description"
                placeholder="e.g., A specific release date has been announced"
                value={conditionDescription}
                onChange={(e) => onConditionDescriptionChange(e.target.value)}
                className="min-h-[80px] resize-none"
                rows={3}
              />
              <p className="text-xs text-muted-foreground">
                Describe what change or condition should trigger a notification
              </p>
            </CollapsibleContent>
          </Collapsible>

          {/* Re-Preview Button */}
          <Button
            type="button"
            variant="outline"
            onClick={onPreview}
            className="w-full"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Preview Again
          </Button>
        </div>
      )}
    </div>
  );
};
