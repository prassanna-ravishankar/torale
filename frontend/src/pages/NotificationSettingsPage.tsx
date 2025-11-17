import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Bell } from 'lucide-react';
import { EmailManagementSection } from '@/components/settings/EmailManagementSection';
import { WebhookConfigSection } from '@/components/settings/WebhookConfigSection';
import { NotificationHistorySection } from '@/components/settings/NotificationHistorySection';
import { ApiKeyManagementSection } from '@/components/settings/ApiKeyManagementSection';

export const NotificationSettingsPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="container mx-auto max-w-4xl py-8 space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <Button
          variant="ghost"
          size="sm"
          className="gap-2"
          onClick={() => navigate('/')}
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Button>
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-primary/10 p-3">
            <Bell className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Notification Settings</h1>
            <p className="text-muted-foreground">
              Manage how you receive notifications from your monitoring tasks
            </p>
          </div>
        </div>
      </div>

      {/* Email Management */}
      <EmailManagementSection />

      {/* Webhook Configuration */}
      <WebhookConfigSection />

      {/* API Key Management */}
      <ApiKeyManagementSection />

      {/* Notification History */}
      <NotificationHistorySection />
    </div>
  );
};
