import React, { useState, useEffect, useRef } from 'react';
import { getErrorMessage } from '@/lib/utils';
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
import { useApi } from '@/hooks/useApi';
import { toast } from 'sonner';
import type { Task, TaskExecution } from '@/types';
import { getResultDisplayText } from '@/types';

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
  const api = useApi();
  const [isLoading, setIsLoading] = useState(false);
  const [execution, setExecution] = useState<TaskExecution | null>(null);
  const [error, setError] = useState<string>('');
  const cancelledRef = useRef(false);

  // Execute task when modal opens, cancel polling on close/unmount
  useEffect(() => {
    if (!open) return;

    cancelledRef.current = false;
    setIsLoading(true);
    setError('');
    setExecution(null);

    let timeoutId: ReturnType<typeof setTimeout>;

    const execute = async () => {
      try {
        const executionResult = await api.executeTask(task.id, true);

        let attempts = 0;
        const maxAttempts = 30;
        const pollInterval = 1000;

        const poll = async () => {
          if (cancelledRef.current) return;

          try {
            const executions = await api.getTaskExecutions(task.id);
            if (cancelledRef.current) return;

            const latest = executions.find((e) => e.id === executionResult.id);

            if (latest && (latest.status === 'success' || latest.status === 'failed')) {
              setExecution(latest);
              setIsLoading(false);
              if (latest.status === 'failed') {
                setError(latest.error_message || 'Execution failed');
              }
            } else if (attempts < maxAttempts) {
              attempts++;
              timeoutId = setTimeout(poll, pollInterval);
            } else {
              setIsLoading(false);
              setError('Execution timed out');
            }
          } catch (err) {
            if (!cancelledRef.current) {
              console.error('Poll failed:', err);
              setIsLoading(false);
              setError(getErrorMessage(err, 'Failed to check results'));
            }
          }
        };

        if (!cancelledRef.current) {
          timeoutId = setTimeout(poll, pollInterval);
        }
      } catch (err) {
        if (cancelledRef.current) return;
        console.error('Failed to execute task:', err);
        const message = getErrorMessage(err, "Couldn't run the watch");
        setError(message);
        toast.error(message);
        setIsLoading(false);
      }
    };

    execute();

    return () => {
      cancelledRef.current = true;
      clearTimeout(timeoutId);
    };
  }, [api, open, task.id]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col overflow-hidden border border-ink-6 shadow-ww-md">
        <DialogHeader className="flex-shrink-0 border-b border-ink-6 pb-4">
          <DialogTitle className="text-xl font-medium">Preview: {task.name}</DialogTitle>
          <DialogDescription className="text-ink-3">
            Testing your watch (notifications suppressed)
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto min-h-0 px-1">
          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div className="text-center space-y-2">
                <h3 className="font-medium">Running watch...</h3>
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
              <div className="p-3 bg-ink-8 border border-ink-6">
                <p className="text-[10px] font-mono uppercase text-ink-4 mb-1 tracking-wider">Search Query</p>
                <p className="text-sm text-ink-3">"{task.search_query}"</p>
              </div>

              {(() => {
                const displayText = getResultDisplayText(execution.result);
                return displayText ? (
                  <SearchPreview
                    answer={displayText}
                    conditionMet={!!execution.notification}
                    conditionDescription={task.condition_description}
                    groundingSources={execution.grounding_sources || []}
                    currentState={execution.result.metadata?.current_state}
                    showConditionBadge={true}
                  />
                ) : (
                  <div className="p-4 border border-amber-200 bg-amber-50">
                    <p className="text-sm text-amber-700">
                      The agent completed but did not produce a summary.
                    </p>
                  </div>
                );
              })()}

            </div>
          )}
        </div>

        <DialogFooter className="flex-shrink-0 border-t border-ink-6 pt-4 gap-3">
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
          <Button onClick={() => onOpenChange(false)} className="shadow-ww-sm">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
