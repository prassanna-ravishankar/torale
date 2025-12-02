import React, { useState, useEffect } from 'react';
import { Switch } from '@/components/ui/switch';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Loader2,
  Copy,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Send,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
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
    if (!config.url || !config.secret) {
      toast.error('Webhook URL and secret are required');
      return;
    }

    setIsTesting(true);
    try {
      await api.testWebhook(config.url, config.secret);
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
      <div className="bg-white border-2 border-zinc-200 p-8 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
      </div>
    );
  }

  return (
    <div className="bg-white border-2 border-zinc-200">
      {/* Header */}
      <div className="p-4 border-b border-zinc-200 flex items-center justify-between">
        <p className="text-xs text-zinc-500">
          Configure webhooks to receive notifications via HTTP POST.
        </p>
        {config.url && (
          <span className={`inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono uppercase tracking-wider border ${
            config.enabled
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
              : 'bg-zinc-50 text-zinc-500 border-zinc-200'
          }`}>
            {config.enabled ? <CheckCircle2 className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
            {config.enabled ? 'Active' : 'Inactive'}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Webhook URL */}
        <div className="space-y-2">
          <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
            Webhook URL
          </label>
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="url"
              placeholder="https://your-server.com/webhooks/"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              disabled={isSaving}
              className="flex-1 px-3 py-2 bg-white border-2 border-zinc-200 text-xs sm:text-sm font-mono focus:outline-none focus:border-zinc-900 disabled:opacity-50 disabled:bg-zinc-50"
            />
            <button
              onClick={handleSave}
              disabled={isSaving || !webhookUrl}
              className="px-4 py-2 bg-zinc-900 text-white text-xs sm:text-sm font-mono hover:bg-[hsl(10,90%,55%)] transition-colors disabled:opacity-50 disabled:hover:bg-zinc-900 shrink-0"
            >
              {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save'}
            </button>
          </div>
          <p className="text-[10px] text-zinc-400 font-mono">Must use HTTPS for security</p>
        </div>

        {/* Webhook Secret */}
        {config.secret && (
          <div className="space-y-2">
            <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
              Signing Secret
            </label>
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="flex-1 flex items-center px-3 py-2 bg-zinc-900 text-zinc-300 font-mono text-[10px] sm:text-sm border-2 border-zinc-900 min-w-0">
                <code className="truncate">
                  {showSecret ? config.secret : maskSecret(config.secret)}
                </code>
              </div>
              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => setShowSecret(!showSecret)}
                  className="p-2 border-2 border-zinc-200 text-zinc-600 hover:border-zinc-900 hover:text-zinc-900 transition-colors"
                  title={showSecret ? 'Hide secret' : 'Show secret'}
                >
                  {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
                <button
                  onClick={handleCopySecret}
                  className="p-2 border-2 border-zinc-200 text-zinc-600 hover:border-zinc-900 hover:text-zinc-900 transition-colors"
                  title="Copy secret"
                >
                  {copiedSecret ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
                <button
                  onClick={handleRegenerateSecret}
                  disabled={isSaving}
                  className="p-2 border-2 border-zinc-200 text-zinc-600 hover:border-zinc-900 hover:text-zinc-900 transition-colors disabled:opacity-50"
                  title="Regenerate secret"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
              </div>
            </div>
            <p className="text-[10px] text-zinc-400 font-mono">
              Use this secret to verify webhook signatures. Keep it secure!
            </p>
          </div>
        )}

        {/* Enable/Disable Toggle */}
        {config.secret && (
          <div className="flex items-center justify-between p-3 bg-zinc-50 border border-zinc-200">
            <div>
              <p className="text-sm font-mono text-zinc-900">Enable Webhook</p>
              <p className="text-[10px] text-zinc-500">Receive notifications at this URL</p>
            </div>
            <Switch
              checked={config.enabled}
              onCheckedChange={handleToggleEnabled}
              disabled={isSaving}
              className="data-[state=checked]:bg-zinc-900 data-[state=unchecked]:bg-zinc-200 border-2 border-zinc-900"
            />
          </div>
        )}

        {/* Test Webhook Button */}
        {config.secret && config.enabled && (
          <button
            onClick={handleTest}
            disabled={isTesting}
            className="w-full flex items-center justify-center gap-2 p-3 border-2 border-dashed border-zinc-300 text-zinc-600 hover:border-zinc-900 hover:text-zinc-900 transition-all text-sm font-mono disabled:opacity-50"
          >
            {isTesting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            Test Webhook
          </button>
        )}

        {/* Documentation */}
        <Collapsible open={isDocOpen} onOpenChange={setIsDocOpen}>
          <CollapsibleTrigger className="w-full flex items-center justify-between p-3 bg-zinc-50 border border-zinc-200 hover:bg-zinc-100 transition-colors">
            <span className="text-xs font-mono text-zinc-600">Webhook Documentation</span>
            {isDocOpen ? (
              <ChevronUp className="h-4 w-4 text-zinc-400" />
            ) : (
              <ChevronDown className="h-4 w-4 text-zinc-400" />
            )}
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="bg-zinc-900 text-zinc-300 p-4 space-y-4 text-xs font-mono border-x border-b border-zinc-200">
              <div>
                <h4 className="text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Signature Header</h4>
                <code className="text-emerald-400">X-Torale-Signature: t=&lt;timestamp&gt;,v1=&lt;signature&gt;</code>
              </div>

              <div>
                <h4 className="text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Headers</h4>
                <ul className="space-y-1 text-zinc-400">
                  <li><code className="text-zinc-300">Content-Type:</code> application/json</li>
                  <li><code className="text-zinc-300">User-Agent:</code> Torale-Webhooks/1.0</li>
                  <li><code className="text-zinc-300">X-Torale-Event:</code> task.condition_met</li>
                  <li><code className="text-zinc-300">X-Torale-Delivery:</code> [execution_id]</li>
                </ul>
              </div>

              <div>
                <h4 className="text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Payload</h4>
                <pre className="text-[10px] leading-relaxed overflow-x-auto text-zinc-400">{`{
  "id": "exec_123",
  "event_type": "task.condition_met",
  "created_at": 1699564800,
  "data": {
    "task": { "id": "...", "name": "..." },
    "execution": { "condition_met": true },
    "result": { "answer": "...", "sources": [...] }
  }
}`}</pre>
              </div>

              <div>
                <h4 className="text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Retry Policy</h4>
                <p className="text-zinc-400">Exponential backoff: 1min → 5min → 15min</p>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>
    </div>
  );
};
