import React, { useState, useEffect, useCallback } from 'react';
import {
  Loader2,
  Copy,
  CheckCircle2,
  RefreshCw,
  Send,
  Eye,
  EyeOff,
} from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import { CollapsibleSection, Switch, StatusBadge } from '@/components/torale';
import { getErrorMessage } from '@/lib/utils';
import { toast } from 'sonner';
import type { WebhookConfig } from '@/types';
import styles from './Settings.module.css';

export const WebhookConfigSection: React.FC = () => {
  const api = useApi();
  const [config, setConfig] = useState<WebhookConfig>({ url: null, secret: null, enabled: false });
  const [webhookUrl, setWebhookUrl] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const [copiedSecret, setCopiedSecret] = useState(false);
  const [isDocOpen, setIsDocOpen] = useState(false);

  const loadWebhookConfig = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await api.getWebhookConfig();
      setConfig(response);
      setWebhookUrl(response.url || '');
    } catch (err) {
      toast.error('Failed to load webhook configuration');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void loadWebhookConfig();
  }, [loadWebhookConfig]);

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
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to save webhook configuration'));
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
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to send test webhook'));
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
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to regenerate secret'));
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
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to update webhook status'));
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
      <div className={styles.loadingRow}>
        <Loader2 className="h-4 w-4 animate-spin" />
        loading…
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Status pill (only when configured) */}
      {config.url && (
        <div className="flex justify-end">
          <StatusBadge
            variant={config.enabled ? 'success' : 'paused'}
            label={config.enabled ? 'Active' : 'Inactive'}
            size="sm"
          />
        </div>
      )}

      {/* Webhook URL */}
      <div className={styles.fieldRow}>
        <div className={styles.field}>
          <label>Webhook URL</label>
          <input
            type="url"
            placeholder="https://your-server.com/webhooks/"
            value={webhookUrl}
            onChange={(e) => setWebhookUrl(e.target.value)}
            disabled={isSaving}
          />
        </div>
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving || !webhookUrl}
          className={styles.btnPrimary}
          style={{ alignSelf: 'flex-end' }}
        >
          {isSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
          Save
        </button>
      </div>

      {/* Webhook Secret */}
      {config.secret && (
        <div className={styles.field}>
          <label>Signing secret</label>
          <div className="flex gap-2 items-stretch">
            <div className={styles.secret}>
              <code>{showSecret ? config.secret : maskSecret(config.secret)}</code>
            </div>
            <button
              type="button"
              onClick={() => setShowSecret(!showSecret)}
              className={styles.iconBtn}
              title={showSecret ? 'Hide secret' : 'Show secret'}
              aria-label={showSecret ? 'Hide secret' : 'Show secret'}
            >
              {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
            <button
              type="button"
              onClick={handleCopySecret}
              className={styles.iconBtn}
              title="Copy secret"
              aria-label="Copy secret"
            >
              {copiedSecret ? (
                <CheckCircle2 className="h-4 w-4" style={{ color: 'var(--ww-success)' }} />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </button>
            <button
              type="button"
              onClick={handleRegenerateSecret}
              disabled={isSaving}
              className={styles.iconBtn}
              title="Regenerate secret"
              aria-label="Regenerate secret"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Enable/Disable Toggle */}
      {config.secret && (
        <div className={styles.toggleRow}>
          <div>
            <div className={styles.toggleLabel}>Enabled</div>
            <div className={styles.toggleHint}>Receive notifications at this URL</div>
          </div>
          <Switch
            checked={config.enabled}
            onCheckedChange={handleToggleEnabled}
            disabled={isSaving}
          />
        </div>
      )}

      {/* Test Webhook Button */}
      {config.secret && config.enabled && (
        <div className={styles.actions} style={{ justifyContent: 'flex-start' }}>
          <button
            type="button"
            onClick={handleTest}
            disabled={isTesting}
            className={styles.btnSecondary}
          >
            {isTesting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
            Send test
          </button>
        </div>
      )}

      {/* Documentation */}
      <CollapsibleSection
        title="Webhook documentation"
        open={isDocOpen}
        onOpenChange={setIsDocOpen}
      >
        <div
          className="p-4 space-y-4 text-xs"
          style={{
            background: 'var(--ww-ink-1)',
            color: 'var(--ww-ink-7)',
            fontFamily: 'var(--ww-font-mono)',
            borderRadius: 'var(--ww-radius-sm)',
          }}
        >
          <div>
            <h4 className={styles.sectionLabel} style={{ marginBottom: 6 }}>Signature header</h4>
            <code style={{ color: 'var(--ww-success)' }}>
              X-Webwhen-Signature: t=&lt;timestamp&gt;,v1=&lt;signature&gt;
            </code>
          </div>

          <div>
            <h4 className={styles.sectionLabel} style={{ marginBottom: 6 }}>Headers</h4>
            <ul className="space-y-1" style={{ color: 'var(--ww-ink-5)' }}>
              <li><code style={{ color: 'var(--ww-ink-7)' }}>Content-Type:</code> application/json</li>
              <li><code style={{ color: 'var(--ww-ink-7)' }}>User-Agent:</code> Webwhen-Webhooks/1.0</li>
              <li><code style={{ color: 'var(--ww-ink-7)' }}>X-Webwhen-Event:</code> task.condition_met</li>
              <li><code style={{ color: 'var(--ww-ink-7)' }}>X-Webwhen-Delivery:</code> [execution_id]</li>
            </ul>
          </div>

          <div>
            <h4 className={styles.sectionLabel} style={{ marginBottom: 6 }}>Payload</h4>
            <pre className="text-[10px] leading-relaxed overflow-x-auto" style={{ color: 'var(--ww-ink-5)' }}>{`{
  "id": "exec_123",
  "event_type": "task.condition_met",
  "created_at": 1699564800,
  "data": {
    "task": { "id": "...", "name": "..." },
    "execution": { "notification": "..." },
    "result": { "answer": "...", "sources": [...] }
  }
}`}</pre>
          </div>

          <div>
            <h4 className={styles.sectionLabel} style={{ marginBottom: 6 }}>Retry policy</h4>
            <p style={{ color: 'var(--ww-ink-5)' }}>Exponential backoff: 1min → 5min → 15min</p>
          </div>
        </div>
      </CollapsibleSection>
    </div>
  );
};
