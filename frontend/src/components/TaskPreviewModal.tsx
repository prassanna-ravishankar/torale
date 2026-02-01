import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { SearchPreview } from '@/components/SearchPreview';
import { Loader2, Edit, ExternalLink } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import type { Task, TaskExecution } from '@/types';

interface TaskPreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task;
  onEdit: (taskId: string) => void;
  onViewHistory: (taskId: string) => void;
}

export const TaskPreviewModal: React.FC<TaskPreviewModalProps> = ({
  open,
  onOpenChange,
  task,
  onEdit,
  onViewHistory,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [execution, setExecution] = useState<TaskExecution | null>(null);
  const [error, setError] = useState<string>('');

  // Execute task when modal opens
  useEffect(() => {
    if (open && task) {
      handleExecute();
    }
  }, [open, task?.id]);

  const handleExecute = async () => {
    setIsLoading(true);
    setError('');
    setExecution(null);

    try {
      // Execute with suppress_notifications=true
      const executionResult = await api.executeTask(task.id, true);

      // Poll for results
      let attempts = 0;
      const maxAttempts = 30; // 30 seconds
      const pollInterval = 1000; // 1 second

      const poll = async () => {
        const executions = await api.getTaskExecutions(task.id);
        const latest = executions.find((e) => e.id === executionResult.id);

        if (latest && (latest.status === 'success' || latest.status === 'failed')) {
          setExecution(latest);
          setIsLoading(false);
          if (latest.status === 'failed') {
            setError(latest.error_message || 'Execution failed');
          }
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, pollInterval);
        } else {
          setIsLoading(false);
          setError('Execution timed out');
        }
      };

      setTimeout(poll, pollInterval);
    } catch (err) {
      console.error('Failed to execute task:', err);
      const message = err instanceof Error ? err.message : 'Failed to run task';
      setError(message);
      toast.error(message);
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col overflow-hidden border-2 border-zinc-900 shadow-brutalist-lg">
        <DialogHeader className="flex-shrink-0 border-b-2 border-zinc-100 pb-4">
          <DialogTitle className="text-xl font-bold font-grotesk">Preview: {task.name}</DialogTitle>
          <DialogDescription className="text-zinc-500">
            Testing your monitoring task (notifications suppressed)
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto min-h-0 px-1">
          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div className="text-center space-y-2">
                <h3 className="font-medium">Running task...</h3>
                <p className="text-sm text-muted-foreground">
                  This may take a few seconds
                </p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="p-4 border border-destructive/50 bg-destructive/10 rounded-lg">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          {/* Results */}
          {execution && execution.status === 'success' && execution.result && (
            <div className="space-y-4">
              <div className="p-3 bg-zinc-50 border-2 border-zinc-100">
                <p className="text-[10px] font-mono uppercase text-zinc-400 mb-1 tracking-wider">Search Query</p>
                <p className="text-sm text-zinc-600">"{task.search_query}"</p>
              </div>

              <SearchPreview
                answer={execution.result.summary}
                conditionMet={execution.condition_met || false}
                conditionDescription={task.condition_description}
                groundingSources={execution.grounding_sources || []}
                currentState={execution.result.metadata?.current_state}
                showConditionBadge={true}
              />

              {execution.change_summary && (
                <div className="p-3 bg-zinc-50 border-2 border-zinc-100">
                  <p className="text-[10px] font-mono uppercase text-zinc-400 mb-1 tracking-wider">What Changed</p>
                  <p className="text-sm text-zinc-600">{execution.change_summary}</p>
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="flex-shrink-0 border-t-2 border-zinc-100 pt-4 gap-3">
          <Button
            variant="outline"
            onClick={() => {
              onEdit(task.id);
              onOpenChange(false);
            }}
          >
            <Edit className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              onViewHistory(task.id);
              onOpenChange(false);
            }}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            View History
          </Button>
          <Button onClick={() => onOpenChange(false)} className="shadow-brutalist">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
