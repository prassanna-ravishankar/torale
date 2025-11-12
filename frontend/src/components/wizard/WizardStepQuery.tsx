import React from 'react';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TaskTemplate } from '@/types';

interface WizardStepQueryProps {
  searchQuery: string;
  onSearchQueryChange: (value: string) => void;
  name: string;
  onNameChange: (value: string) => void;
  errors: {
    searchQuery?: string;
    name?: string;
  };
  selectedTemplate?: TaskTemplate | null;
  onChangeTemplate?: () => void;
}

export const WizardStepQuery: React.FC<WizardStepQueryProps> = ({
  searchQuery,
  onSearchQueryChange,
  name,
  onNameChange,
  errors,
  selectedTemplate,
  onChangeTemplate,
}) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">What do you want to monitor?</h2>
        <p className="text-muted-foreground">
          Enter your search query. We'll check for updates and notify you when conditions are met.
        </p>
      </div>

      {/* Selected Template Badge */}
      {selectedTemplate && onChangeTemplate && (
        <div className="p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline">Using template:</Badge>
              <span className="text-sm font-medium">{selectedTemplate.name}</span>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onChangeTemplate}
            >
              Change Template
            </Button>
          </div>
        </div>
      )}

      {/* Task Name */}
      <div className="space-y-2">
        <Label htmlFor="task-name" className="flex items-center gap-2">
          Task Name
        </Label>
        <Input
          id="task-name"
          placeholder="e.g., iPhone 16 Release Monitor"
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          className={cn(errors.name && "border-destructive")}
        />
        {errors.name && (
          <p className="text-xs text-destructive flex items-center gap-1.5">
            <AlertCircle className="h-3 w-3" />
            {errors.name}
          </p>
        )}
      </div>

      {/* Search Query */}
      <div className="space-y-2">
        <Label htmlFor="search-query" className="flex items-center gap-2">
          <Search className="h-4 w-4" />
          Search Query
        </Label>
        <Textarea
          id="search-query"
          placeholder="e.g., When is the iPhone 16 being released?"
          value={searchQuery}
          onChange={(e) => onSearchQueryChange(e.target.value)}
          className={cn(
            "min-h-[120px] resize-none",
            errors.searchQuery && "border-destructive"
          )}
          rows={4}
        />
        {errors.searchQuery && (
          <p className="text-xs text-destructive flex items-center gap-1.5">
            <AlertCircle className="h-3 w-3" />
            {errors.searchQuery}
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          Ask a question or describe what information you want to track
        </p>
      </div>

      {/* Examples */}
      <div className="p-4 bg-muted/50 rounded-lg space-y-2">
        <p className="text-sm font-medium">Examples:</p>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>• "When is the next iPhone release date?"</li>
          <li>• "What is the price of Tesla Model 3?"</li>
          <li>• "Is GPT-5 available yet?"</li>
          <li>• "When do summer pool memberships open?"</li>
        </ul>
      </div>
    </div>
  );
};
