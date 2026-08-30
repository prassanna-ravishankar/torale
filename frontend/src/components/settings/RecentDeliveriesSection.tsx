import React, { useState, useEffect, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import type { WebhookDelivery, NotificationSend } from '@/types';
import { StatusBadge, type StatusVariant } from '@/components/torale';
import { formatTimeAgo } from '@/lib/utils';
import styles from './Settings.module.css';

export const RecentDeliveriesSection: React.FC = () => {
  const api = useApi();
  const [activeTab, setActiveTab] = useState<'emails' | 'webhooks'>('emails');
  const [emailSends, setEmailSends] = useState<NotificationSend[]>([]);
  const [webhookDeliveries, setWebhookDeliveries] = useState<WebhookDelivery[]>([]);
  const [isLoadingEmails, setIsLoadingEmails] = useState(true);
  const [isLoadingWebhooks, setIsLoadingWebhooks] = useState(true);

  const loadHistory = useCallback(async () => {
    setIsLoadingEmails(true);
    try {
      const emailResponse = await api.getNotificationSends({
        notification_type: 'email',
        limit: 10,
      });
      setEmailSends(emailResponse.sends || []);
    } catch (err) {
      console.error('Failed to load email history:', err);
    } finally {
      setIsLoadingEmails(false);
    }

    setIsLoadingWebhooks(true);
    try {
      const webhookResponse = await api.getWebhookDeliveries({ limit: 10 });
      setWebhookDeliveries(webhookResponse.deliveries || []);
    } catch (err) {
      console.error('Failed to load webhook history:', err);
    } finally {
      setIsLoadingWebhooks(false);
    }
  }, [api]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const getStatusVariant = (status: string): StatusVariant => {
    switch (status) {
      case 'success':
        return 'success';
      case 'failed':
        return 'failed';
      case 'retrying':
        return 'pending';
      default:
        return 'unknown';
    }
  };

  const getDotClass = (status: string) => {
    switch (status) {
      case 'success':
        return styles.runDotSuccess;
      case 'failed':
        return styles.runDotDanger;
      case 'retrying':
        return styles.runDotInfo;
      default:
        return '';
    }
  };

  const renderLoading = () => (
    <div className={styles.loadingRow}>
      <Loader2 className="h-4 w-4 animate-spin" />
      loading…
    </div>
  );

  const formatTimestamp = (iso: string) => {
    const d = new Date(iso);
    const today = new Date();
    if (d.toDateString() === today.toDateString()) {
      return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    }
    return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
  };

  return (
    <>
      {/* Segmented tabs */}
      <div className={styles.tabs} style={{ marginBottom: 16 }}>
        <button
          type="button"
          onClick={() => setActiveTab('emails')}
          className={`${styles.tab} ${activeTab === 'emails' ? styles.tabActive : ''}`}
        >
          Emails
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('webhooks')}
          className={`${styles.tab} ${activeTab === 'webhooks' ? styles.tabActive : ''}`}
        >
          Webhooks
        </button>
      </div>

      {activeTab === 'emails' ? (
        isLoadingEmails ? (
          renderLoading()
        ) : emailSends.length === 0 ? (
          <div className={styles.emptyHint}>No emails sent yet.</div>
        ) : (
          <div className={styles.runs}>
            {emailSends.map((send) => (
              <div key={send.id} className={styles.run}>
                <span className={styles.runT}>{formatTimestamp(send.created_at)}</span>
                <span className={`${styles.runDot} ${getDotClass(send.status)}`} />
                <span className={styles.runB}>
                  <span style={{ color: 'var(--ww-ink-0)' }}>{send.recipient}</span>
                  <span style={{ color: 'var(--ww-ink-4)', marginLeft: 8 }}>
                    · {formatTimeAgo(send.created_at)}
                  </span>
                </span>
                <StatusBadge variant={getStatusVariant(send.status)} size="sm" />
              </div>
            ))}
          </div>
        )
      ) : isLoadingWebhooks ? (
        renderLoading()
      ) : webhookDeliveries.length === 0 ? (
        <div className={styles.emptyHint}>No webhook deliveries yet.</div>
      ) : (
        <div className={styles.runs}>
          {webhookDeliveries.map((delivery) => {
            let host = delivery.webhook_url;
            try {
              host = new URL(delivery.webhook_url).host;
            } catch {
              /* keep raw URL */
            }
            return (
              <div key={delivery.id} className={styles.run}>
                <span className={styles.runT}>{formatTimestamp(delivery.created_at)}</span>
                <span className={`${styles.runDot} ${getDotClass(delivery.status)}`} />
                <span className={styles.runB}>
                  <span style={{ color: 'var(--ww-ink-0)' }}>{host}</span>
                  {delivery.http_status_code && (
                    <span style={{ color: 'var(--ww-ink-4)', marginLeft: 8 }}>
                      · {delivery.http_status_code}
                    </span>
                  )}
                  {delivery.attempts > 1 && (
                    <span style={{ color: 'var(--ww-ink-4)', marginLeft: 8 }}>
                      · attempt {delivery.attempts}
                    </span>
                  )}
                </span>
                <StatusBadge variant={getStatusVariant(delivery.status)} size="sm" />
              </div>
            );
          })}
        </div>
      )}
    </>
  );
};
