import React, { useState, useEffect } from 'react';
import Neocron from 'neocron';
import cronstrue from 'cronstrue';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CronDisplay } from '@/components/ui/CronDisplay';
import { AlertCircle } from 'lucide-react';

interface CustomScheduleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialValue: string;
  onSave: (cronString: string) => void;
}

export const CustomScheduleDialog: React.FC<CustomScheduleDialogProps> = ({
  open,
  onOpenChange,
  initialValue,
  onSave,
}) => {
  const [cronString, setCronString] = useState(initialValue);
  const [isValid, setIsValid] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  // Reset to initial value when dialog opens
  useEffect(() => {
    if (open) {
      setCronString(initialValue);
      validateCron(initialValue);
    }
  }, [open, initialValue]);

  // Validate cron expression
  const validateCron = (cron: string) => {
    try {
      cronstrue.toString(cron, { throwExceptionOnParseError: true });
      setIsValid(true);
      setErrorMessage('');
      return true;
    } catch (error) {
      setIsValid(false);
      setErrorMessage(error instanceof Error ? error.message : 'Invalid cron expression');
      return false;
    }
  };

  // Handle cron string change from Neocron
  const handleCronChange = (newCron: string) => {
    setCronString(newCron);
    validateCron(newCron);
  };

  // Handle save
  const handleSave = () => {
    if (isValid) {
      onSave(cronString);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Custom Schedule</DialogTitle>
          <DialogDescription>
            Create a custom schedule using the visual builder or enter a cron expression directly.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Neocron Component */}
          <div className="rounded-lg border p-4">
            <Neocron
              cronString={cronString}
              setCronString={handleCronChange}
              defaultCronString={initialValue}
              disableInput={false}
              disableExplainerText={false}
            />
          </div>

          {/* Validation Error */}
          {!isValid && errorMessage && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          )}

          {/* Preview */}
          {isValid && (
            <div className="rounded-lg bg-muted/50 p-3">
              <p className="text-sm font-medium mb-1">Preview:</p>
              <p className="text-sm text-muted-foreground">
                This task will run{' '}
                <CronDisplay
                  cron={cronString}
                  showRaw={false}
                  className="text-foreground font-medium lowercase"
                />
              </p>
              <p className="text-xs text-muted-foreground mt-1 font-mono">
                Cron: {cronString}
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!isValid}
          >
            Save Schedule
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
