import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Loader2,
  Webhook,
  Copy,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Send,
  Eye,
  EyeOff,
  ChevronDown,
  Info,
} from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import type { WebhookConfig } from '@/types';

export const WebhookConfigSection: React.FC = () => {
  const [config, setConfig] = useState<WebhookConfig>({ url: null, secret: null, enabled: false });
  const [webhookUrl, setWebhookUrl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const [copiedSecret, setCopiedSecret] = useState(false);
  const [isDocOpen, setIsDocOpen] = useState(false);

  useEffect(() => {
    loadWebhookConfig();
  }, []);

  const loadWebhookConfig = async () => {
    setIsLoading(true);
    try {
      const response = await api.getWebhookConfig();
      setConfig(response);
      setWebhookUrl(response.url || '');
    } catch (err: any) {
      toast.error('Failed to load webhook configuration');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!webhookUrl) {
      toast.error('Please enter a webhook URL');
      return;
    }

    if (!webhookUrl.startsWith('https://')) {
      toast.error('Webhook URL must use HTTPS');
      return;
    }

    setIsSaving(true);
    try {
      const response = await api.updateWebhookConfig(webhookUrl, config.enabled);
      setConfig(response);
      setWebhookUrl(response.url || '');
      toast.success('Webhook configuration saved');
    } catch (err: any) {
      toast.error(err.message || 'Failed to save webhook configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    setIsTesting(true);
    try {
      const response = await api.testWebhook();
      toast.success('Test webhook sent successfully!');
    } catch (err: any) {
      toast.error(err.message || 'Failed to send test webhook');
    } finally {
      setIsTesting(false);
    }
  };

  const handleCopySecret = () => {
    if (config.secret) {
      navigator.clipboard.writeText(config.secret);
      setCopiedSecret(true);
      toast.success('Secret copied to clipboard');
      setTimeout(() => setCopiedSecret(false), 2000);
    }
  };

  const handleRegenerateSecret = async () => {
    if (!webhookUrl) {
      toast.error('Please enter a webhook URL first');
      return;
    }

    setIsSaving(true);
    try {
      // Updating with the same URL will regenerate the secret
      const response = await api.updateWebhookConfig(webhookUrl, config.enabled);
      setConfig(response);
      toast.success('Webhook secret regenerated');
    } catch (err: any) {
      toast.error(err.message || 'Failed to regenerate secret');
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleEnabled = async (enabled: boolean) => {
    if (!webhookUrl || !config.secret) {
      toast.error('Please configure webhook URL first');
      return;
    }

    setIsSaving(true);
    try {
      const response = await api.updateWebhookConfig(webhookUrl, enabled);
      setConfig(response);
      toast.success(enabled ? 'Webhook enabled' : 'Webhook disabled');
    } catch (err: any) {
      toast.error(err.message || 'Failed to update webhook status');
    } finally {
      setIsSaving(false);
    }
  };

  const maskSecret = (secret: string | null) => {
    if (!secret) return '';
    return `${secret.slice(0, 8)}...${secret.slice(-8)}`;
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Webhook Configuration</CardTitle>
        <CardDescription>
          Set up a default webhook URL to receive task notifications. Tasks can override this with
          custom webhooks.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Webhook URL */}
        <div className="space-y-2">
          <Label htmlFor="webhook-url">Webhook URL</Label>
          <div className="flex gap-2">
            <Input
              id="webhook-url"
              type="url"
              placeholder="https://your-server.com/webhooks/torale"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              disabled={isSaving}
            />
            <Button onClick={handleSave} disabled={isSaving || !webhookUrl}>
              {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">Must use HTTPS for security</p>
        </div>

        {/* Webhook Secret */}
        {config.secret && (
          <div className="space-y-2">
            <Label>Webhook Secret</Label>
            <div className="flex gap-2">
              <div className="flex-1 flex items-center rounded-md border px-3 py-2 bg-muted font-mono text-sm">
                {showSecret ? config.secret : maskSecret(config.secret)}
              </div>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setShowSecret(!showSecret)}
                title={showSecret ? 'Hide secret' : 'Show secret'}
              >
                {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={handleCopySecret}
                title="Copy secret"
              >
                {copiedSecret ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={handleRegenerateSecret}
                disabled={isSaving}
                title="Regenerate secret"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
            <Alert>
              <Info className="h-4 w-4" />
              <AlertDescription>
                Use this secret to verify webhook signatures on your server. Keep it secure!
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Enable/Disable Toggle */}
        {config.secret && (
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <Label htmlFor="webhook-enabled">Enable Webhook</Label>
              <p className="text-sm text-muted-foreground">
                Receive notifications at this webhook URL
              </p>
            </div>
            <Switch
              id="webhook-enabled"
              checked={config.enabled}
              onCheckedChange={handleToggleEnabled}
              disabled={isSaving}
            />
          </div>
        )}

        {/* Test Webhook Button */}
        {config.secret && config.enabled && (
          <Button onClick={handleTest} disabled={isTesting} variant="outline" className="w-full">
            {isTesting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {!isTesting && <Send className="mr-2 h-4 w-4" />}
            Test Webhook
          </Button>
        )}

        {/* Status Badge */}
        {config.url && (
          <div className="flex items-center gap-2">
            <Webhook className="h-4 w-4" />
            <span className="text-sm text-muted-foreground">Status:</span>
            {config.enabled ? (
              <Badge variant="secondary" className="gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Active
              </Badge>
            ) : (
              <Badge variant="outline" className="gap-1">
                <AlertCircle className="h-3 w-3" />
                Inactive
              </Badge>
            )}
          </div>
        )}

        {/* Documentation */}
        <Collapsible open={isDocOpen} onOpenChange={setIsDocOpen}>
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between">
              <span className="flex items-center gap-2">
                <Info className="h-4 w-4" />
                Webhook Documentation
              </span>
              <ChevronDown
                className={`h-4 w-4 transition-transform ${isDocOpen ? 'rotate-180' : ''}`}
              />
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-4 pt-4">
            <div className="rounded-lg border p-4 space-y-3 text-sm">
              <div>
                <h4 className="font-semibold mb-2">Signature Verification</h4>
                <p className="text-muted-foreground mb-2">
                  Webhooks are signed using HMAC-SHA256. Verify the signature in the{' '}
                  <code className="bg-muted px-1 rounded">X-Torale-Signature</code> header:
                </p>
                <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
                  {`X-Torale-Signature: t=<timestamp>,v1=<signature>`}
                </pre>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Webhook Headers</h4>
                <ul className="space-y-1 text-muted-foreground">
                  <li>
                    <code className="bg-muted px-1 rounded">Content-Type: application/json</code>
                  </li>
                  <li>
                    <code className="bg-muted px-1 rounded">User-Agent: Torale-Webhooks/1.0</code>
                  </li>
                  <li>
                    <code className="bg-muted px-1 rounded">
                      X-Torale-Event: task.condition_met
                    </code>
                  </li>
                  <li>
                    <code className="bg-muted px-1 rounded">X-Torale-Delivery: [execution_id]</code>
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Payload Format</h4>
                <pre className="bg-muted p-3 rounded text-xs overflow-x-auto">
                  {`{
  "id": "exec_123",
  "event_type": "task.condition_met",
  "created_at": 1699564800,
  "data": {
    "task": { "id": "...", "name": "..." },
    "execution": { "condition_met": true },
    "result": { "answer": "...", "grounding_sources": [...] }
  }
}`}
                </pre>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Retry Policy</h4>
                <p className="text-muted-foreground">
                  Failed webhooks are automatically retried with exponential backoff: 1min → 5min →
                  15min
                </p>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  );
};
