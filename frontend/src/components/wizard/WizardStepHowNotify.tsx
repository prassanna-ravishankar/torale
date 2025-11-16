import React from 'react';
import { Card } from '@/components/ui/card';
import { Bell } from 'lucide-react';
import { NotificationChannelSelector } from '@/components/notifications/NotificationChannelSelector';
import type { NotificationConfig } from '@/types';

interface WizardStepHowNotifyProps {
  notifications: NotificationConfig[];
  onNotificationsChange: (value: NotificationConfig[]) => void;
}

export const WizardStepHowNotify: React.FC<WizardStepHowNotifyProps> = ({
  notifications,
  onNotificationsChange,
}) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">Notification Channels</h2>
        <p className="text-muted-foreground">
          Choose how you want to receive notifications when conditions are met.
        </p>
      </div>

      {/* Notification Channel Selector */}
      <NotificationChannelSelector value={notifications} onChange={onNotificationsChange} />

      {/* Info Card */}
      <Card className="p-4 bg-muted/50">
        <div className="flex items-start gap-3">
          <Bell className="h-5 w-5 text-muted-foreground mt-0.5" />
          <div className="space-y-1">
            <p className="text-sm font-medium">Default Configuration</p>
            <p className="text-xs text-muted-foreground">
              By default, notifications will be sent to your Clerk email address. You can customize
              this by expanding the advanced settings above, or configure default webhooks in{' '}
              <a href="/settings/notifications" className="underline hover:text-foreground">
                Settings
              </a>
              .
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
