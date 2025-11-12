import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card } from '@/components/ui/card';
import { Clock, Bell } from 'lucide-react';
import { CronDisplay } from '@/components/ui/CronDisplay';
import { CustomScheduleDialog } from '@/components/ui/CustomScheduleDialog';

type NotifyBehavior = 'once' | 'always' | 'track_state';

interface WizardStepScheduleProps {
  schedule: string;
  onScheduleChange: (value: string) => void;
  notifyBehavior: NotifyBehavior;
  onNotifyBehaviorChange: (value: NotifyBehavior) => void;
}

const SCHEDULE_PRESETS = [
  { value: '0 9 * * *', label: 'Daily at 9:00 AM' },
  { value: '0 */6 * * *', label: 'Every 6 hours' },
  { value: '0 */3 * * *', label: 'Every 3 hours' },
  { value: '0 * * * *', label: 'Every hour' },
  { value: '0 0 * * 1', label: 'Weekly on Monday' },
  { value: '__custom__', label: 'Custom schedule...', isSpecial: true },
];

export const WizardStepSchedule: React.FC<WizardStepScheduleProps> = ({
  schedule,
  onScheduleChange,
  notifyBehavior,
  onNotifyBehaviorChange,
}) => {
  const [customDialogOpen, setCustomDialogOpen] = useState(false);

  // Check if current schedule is a preset (exclude the custom option itself)
  const isCustomSchedule = !SCHEDULE_PRESETS.filter((p) => p.value !== '__custom__').some((p) => p.value === schedule);

  // Get display value for select
  const getSelectValue = () => {
    if (isCustomSchedule) {
      return '__custom__';
    }
    return schedule;
  };

  // Handle schedule selection from dropdown
  const handleScheduleChange = (value: string) => {
    if (value === '__custom__') {
      setCustomDialogOpen(true);
    } else {
      onScheduleChange(value);
    }
  };

  // Handle custom schedule save
  const handleCustomScheduleSave = (cronString: string) => {
    onScheduleChange(cronString);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">Schedule & Notifications</h2>
        <p className="text-muted-foreground">
          Choose when to check for updates and how you want to be notified.
        </p>
      </div>

      {/* Check Frequency */}
      <div className="space-y-3">
        <Label htmlFor="schedule" className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Check Frequency
          <span className="text-destructive">*</span>
        </Label>
        <Select value={getSelectValue()} onValueChange={handleScheduleChange} required>
          <SelectTrigger id="schedule">
            <SelectValue placeholder="Select a schedule" />
          </SelectTrigger>
          <SelectContent>
            {SCHEDULE_PRESETS.map((preset) => (
              <SelectItem key={preset.value} value={preset.value}>
                {preset.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {isCustomSchedule && (
          <p className="text-xs text-muted-foreground">
            Using custom schedule: <span className="font-mono">{schedule}</span>
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          How often should we check for updates?
        </p>
      </div>

      {/* Notify Behavior */}
      <div className="space-y-3">
        <Label className="flex items-center gap-2">
          <Bell className="h-4 w-4" />
          Notification Behavior
        </Label>
        <RadioGroup
          value={notifyBehavior}
          onValueChange={(value) => onNotifyBehaviorChange(value as NotifyBehavior)}
          className="space-y-3"
        >
          <Card className="p-4 cursor-pointer hover:border-primary transition-colors">
            <div className="flex items-start gap-3">
              <RadioGroupItem value="track_state" id="track_state" className="mt-1" />
              <div className="flex-1 space-y-1">
                <Label htmlFor="track_state" className="cursor-pointer font-medium">
                  When information changes
                </Label>
                <p className="text-sm text-muted-foreground">
                  Get notified when the information changes from the last check (recommended)
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-4 cursor-pointer hover:border-primary transition-colors">
            <div className="flex items-start gap-3">
              <RadioGroupItem value="once" id="once" className="mt-1" />
              <div className="flex-1 space-y-1">
                <Label htmlFor="once" className="cursor-pointer font-medium">
                  Once only
                </Label>
                <p className="text-sm text-muted-foreground">
                  Get notified the first time the condition is met, then stop monitoring
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-4 cursor-pointer hover:border-primary transition-colors">
            <div className="flex items-start gap-3">
              <RadioGroupItem value="always" id="always" className="mt-1" />
              <div className="flex-1 space-y-1">
                <Label htmlFor="always" className="cursor-pointer font-medium">
                  Every time
                </Label>
                <p className="text-sm text-muted-foreground">
                  Get notified every time the condition is met (can be noisy)
                </p>
              </div>
            </div>
          </Card>
        </RadioGroup>
      </div>

      {/* Summary Card */}
      <Card className="p-4 bg-muted/50">
        <p className="text-sm font-medium mb-2">Summary:</p>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li className="flex items-center gap-1">
            • We'll check{' '}
            <CronDisplay cron={schedule} showRaw={false} className="text-foreground font-medium lowercase" />
          </li>
          <li>
            • You'll be notified{' '}
            <span className="text-foreground font-medium">
              {notifyBehavior === 'once' && 'the first time only'}
              {notifyBehavior === 'always' && 'every time the condition is met'}
              {notifyBehavior === 'track_state' && 'when the information changes'}
            </span>
          </li>
        </ul>
      </Card>

      {/* Custom Schedule Dialog */}
      <CustomScheduleDialog
        open={customDialogOpen}
        onOpenChange={setCustomDialogOpen}
        initialValue={schedule}
        onSave={handleCustomScheduleSave}
      />
    </div>
  );
};
