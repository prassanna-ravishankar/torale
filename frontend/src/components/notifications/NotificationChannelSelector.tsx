import React, { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Mail, Webhook, ChevronDown, Settings2, AlertCircle, ExternalLink } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';
import type { NotificationConfig } from '@/types';

interface NotificationChannelSelectorProps {
  value: NotificationConfig[];
  onChange: (notifications: NotificationConfig[]) => void;
}

export const NotificationChannelSelector: React.FC<NotificationChannelSelectorProps> = ({
  value,
  onChange,
}) => {
  const { user } = useAuth();
  const clerkEmail = user?.email;

  const [emailEnabled, setEmailEnabled] = useState(true); // Default to email enabled
  const [webhookEnabled, setWebhookEnabled] = useState(false);
  const [verifiedEmails, setVerifiedEmails] = useState<string[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<string>('default');
  const [customWebhookUrl, setCustomWebhookUrl] = useState('');
  const [useDefaultWebhook, setUseDefaultWebhook] = useState(true);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [isLoadingEmails, setIsLoadingEmails] = useState(false);

  // Load verified emails
  useEffect(() => {
    loadVerifiedEmails();
  }, []);

  // Update parent when selections change
  useEffect(() => {
    const notifications: NotificationConfig[] = [];

    if (emailEnabled) {
      notifications.push({
        type: 'email',
        address: selectedEmail === 'default' ? clerkEmail : selectedEmail,
      });
    }

    if (webhookEnabled) {
      notifications.push({
        type: 'webhook',
        url: useDefaultWebhook ? undefined : customWebhookUrl || undefined,
      });
    }

    onChange(notifications);
  }, [emailEnabled, webhookEnabled, selectedEmail, customWebhookUrl, useDefaultWebhook, clerkEmail]);

  const loadVerifiedEmails = async () => {
    setIsLoadingEmails(true);
    try {
      const response = await api.getVerifiedEmails();
      setVerifiedEmails(response.verified_emails || []);
    } catch (err: any) {
      console.error('Failed to load verified emails:', err);
    } finally {
      setIsLoadingEmails(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Simple Channel Selection */}
      <div className="space-y-3">
        <Label>Notification Channels</Label>

        {/* Email Channel */}
        <Card className="p-4">
          <div className="flex items-start gap-3">
            <Checkbox
              id="email-channel"
              checked={emailEnabled}
              onCheckedChange={(checked) => setEmailEnabled(checked as boolean)}
            />
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4" />
                <Label htmlFor="email-channel" className="font-medium cursor-pointer">
                  Email Notifications
                </Label>
              </div>
              <p className="text-sm text-muted-foreground">
                Receive notifications at {clerkEmail || 'your Clerk email'}
              </p>
            </div>
          </div>
        </Card>

        {/* Webhook Channel */}
        <Card className="p-4">
          <div className="flex items-start gap-3">
            <Checkbox
              id="webhook-channel"
              checked={webhookEnabled}
              onCheckedChange={(checked) => setWebhookEnabled(checked as boolean)}
            />
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <Webhook className="h-4 w-4" />
                <Label htmlFor="webhook-channel" className="font-medium cursor-pointer">
                  Webhook Notifications
                </Label>
              </div>
              <p className="text-sm text-muted-foreground">
                Send notifications to your configured webhook endpoint
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Advanced Configuration */}
      <Collapsible open={isAdvancedOpen} onOpenChange={setIsAdvancedOpen}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="w-full justify-between">
            <span className="flex items-center gap-2">
              <Settings2 className="h-4 w-4" />
              Advanced Notification Settings
            </span>
            <ChevronDown
              className={`h-4 w-4 transition-transform ${isAdvancedOpen ? 'rotate-180' : ''}`}
            />
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent className="space-y-4 pt-4">
          {/* Email Settings */}
          {emailEnabled && (
            <div className="space-y-2">
              <Label htmlFor="email-select">Email Address</Label>
              <Select value={selectedEmail} onValueChange={setSelectedEmail}>
                <SelectTrigger id="email-select">
                  <SelectValue placeholder="Select email" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">
                    {clerkEmail || 'Clerk Email'} (Default)
                  </SelectItem>
                  {verifiedEmails.map((email) => (
                    <SelectItem key={email} value={email}>
                      {email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {verifiedEmails.length === 0
                    ? 'No custom emails verified'
                    : `${verifiedEmails.length} verified email(s)`}
                </p>
                <Link to="/settings/notifications">
                  <Button variant="link" size="sm" className="h-auto p-0 gap-1">
                    Manage emails
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </div>
          )}

          {/* Webhook Settings */}
          {webhookEnabled && (
            <div className="space-y-3">
              <Label>Webhook Configuration</Label>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="use-default-webhook"
                    checked={useDefaultWebhook}
                    onCheckedChange={(checked) => setUseDefaultWebhook(checked as boolean)}
                  />
                  <Label htmlFor="use-default-webhook" className="cursor-pointer">
                    Use default webhook from settings
                  </Label>
                </div>

                {!useDefaultWebhook && (
                  <div className="space-y-2">
                    <Label htmlFor="custom-webhook">Custom Webhook URL</Label>
                    <Input
                      id="custom-webhook"
                      type="url"
                      placeholder="https://your-server.com/webhooks/torale"
                      value={customWebhookUrl}
                      onChange={(e) => setCustomWebhookUrl(e.target.value)}
                    />
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription className="text-xs">
                        A unique secret will be generated for this webhook URL
                      </AlertDescription>
                    </Alert>
                  </div>
                )}

                <Link to="/settings/notifications">
                  <Button variant="link" size="sm" className="h-auto p-0 gap-1">
                    Configure default webhook
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </CollapsibleContent>
      </Collapsible>

      {/* Summary */}
      {!isAdvancedOpen && (
        <Alert>
          <Settings2 className="h-4 w-4" />
          <AlertDescription>
            {emailEnabled && !webhookEnabled && 'Email notifications enabled (default Clerk email)'}
            {!emailEnabled && webhookEnabled && 'Webhook notifications enabled'}
            {emailEnabled && webhookEnabled && 'Email and webhook notifications enabled'}
            {!emailEnabled && !webhookEnabled && 'No notification channels selected'}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};
