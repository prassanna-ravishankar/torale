import React, { useState, useEffect } from 'react';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { AlertCircle, Clock } from 'lucide-react';

interface CustomScheduleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initialValue: string;
  onSave: (cronString: string) => void;
}

// Common schedule patterns that can be built with the simple builder
const FREQUENCY_OPTIONS = [
  { value: 'hourly', label: 'Every hour' },
  { value: 'every-n-hours', label: 'Every N hours' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];

const DAYS_OF_WEEK = [
  { value: '0', label: 'Sunday' },
  { value: '1', label: 'Monday' },
  { value: '2', label: 'Tuesday' },
  { value: '3', label: 'Wednesday' },
  { value: '4', label: 'Thursday' },
  { value: '5', label: 'Friday' },
  { value: '6', label: 'Saturday' },
];

export const CustomScheduleDialog: React.FC<CustomScheduleDialogProps> = ({
  open,
  onOpenChange,
  initialValue,
  onSave,
}) => {
  const [activeTab, setActiveTab] = useState<'builder' | 'advanced'>('builder');
  const [cronString, setCronString] = useState(initialValue);
  const [isValid, setIsValid] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');

  // Builder state
  const [frequency, setFrequency] = useState<string>('hourly');
  const [everyNHours, setEveryNHours] = useState<string>('2');
  const [hour, setHour] = useState<string>('9');
  const [minute, setMinute] = useState<string>('0');
  const [dayOfWeek, setDayOfWeek] = useState<string>('1');
  const [dayOfMonth, setDayOfMonth] = useState<string>('1');

  // Reset to initial value when dialog opens
  useEffect(() => {
    if (open) {
      setCronString(initialValue);
      validateCron(initialValue);
      parseInitialCron(initialValue);
    }
  }, [open, initialValue]);

  // Parse initial cron to populate builder
  const parseInitialCron = (cron: string) => {
    const parts = cron.split(' ');
    if (parts.length === 5) {
      const [min, hr, dayM, _month, dayW] = parts;

      setMinute(min);

      // Detect frequency pattern
      if (hr === '*' && dayM === '*' && dayW === '*') {
        setFrequency('hourly');
      } else if (hr.startsWith('*/')) {
        setFrequency('every-n-hours');
        setEveryNHours(hr.replace('*/', ''));
      } else if (dayM === '*' && dayW === '*') {
        setFrequency('daily');
        setHour(hr);
      } else if (dayW !== '*') {
        setFrequency('weekly');
        setHour(hr);
        setDayOfWeek(dayW);
      } else if (dayM !== '*') {
        setFrequency('monthly');
        setHour(hr);
        setDayOfMonth(dayM);
      }
    }
  };

  // Build cron from builder values
  const buildCronFromForm = (): string => {
    switch (frequency) {
      case 'hourly':
        return `${minute} * * * *`;
      case 'every-n-hours':
        return `${minute} */${everyNHours} * * *`;
      case 'daily':
        return `${minute} ${hour} * * *`;
      case 'weekly':
        return `${minute} ${hour} * * ${dayOfWeek}`;
      case 'monthly':
        return `${minute} ${hour} ${dayOfMonth} * *`;
      default:
        return '0 9 * * *';
    }
  };

  // Update cron string when builder values change
  useEffect(() => {
    if (activeTab === 'builder') {
      const newCron = buildCronFromForm();
      setCronString(newCron);
      validateCron(newCron);
    }
  }, [frequency, everyNHours, hour, minute, dayOfWeek, dayOfMonth, activeTab]);

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

  // Handle manual cron string change
  const handleCronChange = (value: string) => {
    setCronString(value);
    validateCron(value);
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
            Build a schedule visually or enter a cron expression directly.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'builder' | 'advanced')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="builder">Quick Builder</TabsTrigger>
            <TabsTrigger value="advanced">Advanced (Cron)</TabsTrigger>
          </TabsList>

          {/* Quick Builder Tab */}
          <TabsContent value="builder" className="space-y-4 py-4">
            {/* Frequency Selection */}
            <div className="space-y-2">
              <Label htmlFor="frequency">Frequency</Label>
              <Select value={frequency} onValueChange={setFrequency}>
                <SelectTrigger id="frequency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FREQUENCY_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Every N Hours Input */}
            {frequency === 'every-n-hours' && (
              <div className="space-y-2">
                <Label htmlFor="every-n-hours">Every N hours</Label>
                <Input
                  id="every-n-hours"
                  type="number"
                  min="1"
                  max="23"
                  value={everyNHours}
                  onChange={(e) => setEveryNHours(e.target.value)}
                />
              </div>
            )}

            {/* Hour and Minute (for daily, weekly, monthly) */}
            {['daily', 'weekly', 'monthly'].includes(frequency) && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="hour">Hour (0-23)</Label>
                  <Input
                    id="hour"
                    type="number"
                    min="0"
                    max="23"
                    value={hour}
                    onChange={(e) => setHour(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="minute">Minute (0-59)</Label>
                  <Input
                    id="minute"
                    type="number"
                    min="0"
                    max="59"
                    value={minute}
                    onChange={(e) => setMinute(e.target.value)}
                  />
                </div>
              </div>
            )}

            {/* Minute only (for hourly, every-n-hours) */}
            {['hourly', 'every-n-hours'].includes(frequency) && (
              <div className="space-y-2">
                <Label htmlFor="minute-only">Minute (0-59)</Label>
                <Input
                  id="minute-only"
                  type="number"
                  min="0"
                  max="59"
                  value={minute}
                  onChange={(e) => setMinute(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Run at this minute past the hour
                </p>
              </div>
            )}

            {/* Day of Week (for weekly) */}
            {frequency === 'weekly' && (
              <div className="space-y-2">
                <Label htmlFor="day-of-week">Day of Week</Label>
                <Select value={dayOfWeek} onValueChange={setDayOfWeek}>
                  <SelectTrigger id="day-of-week">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DAYS_OF_WEEK.map((day) => (
                      <SelectItem key={day.value} value={day.value}>
                        {day.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Day of Month (for monthly) */}
            {frequency === 'monthly' && (
              <div className="space-y-2">
                <Label htmlFor="day-of-month">Day of Month (1-31)</Label>
                <Input
                  id="day-of-month"
                  type="number"
                  min="1"
                  max="31"
                  value={dayOfMonth}
                  onChange={(e) => setDayOfMonth(e.target.value)}
                />
              </div>
            )}
          </TabsContent>

          {/* Advanced Cron Tab */}
          <TabsContent value="advanced" className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="cron-input">Cron Expression</Label>
              <Input
                id="cron-input"
                value={cronString}
                onChange={(e) => handleCronChange(e.target.value)}
                placeholder="0 9 * * *"
                className="font-mono"
              />
              <p className="text-xs text-muted-foreground">
                Format: minute hour day month day-of-week
              </p>
            </div>

            {/* Validation Error */}
            {!isValid && errorMessage && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errorMessage}</AlertDescription>
              </Alert>
            )}
          </TabsContent>
        </Tabs>

        {/* Preview (shown for both tabs) */}
        {isValid && (
          <div className="rounded-lg bg-muted/50 p-4 space-y-2">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              <p className="text-sm font-medium">Schedule Preview</p>
            </div>
            <p className="text-sm text-muted-foreground">
              This task will run{' '}
              <CronDisplay
                cron={cronString}
                showRaw={false}
                className="text-foreground font-medium lowercase"
              />
            </p>
            <p className="text-xs text-muted-foreground font-mono">
              Cron: {cronString}
            </p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={!isValid}>
            Save Schedule
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
