import React, { useState, useEffect } from 'react';
import { Loader2, Mail, Webhook, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { api } from '@/lib/api';
import type { WebhookDelivery, NotificationSend } from '@/types';
import { SectionLabel, BrutalistCard, StatusBadge } from '@/components/torale';

export const NotificationHistorySection: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'emails' | 'webhooks'>('emails');
  const [emailSends, setEmailSends] = useState<NotificationSend[]>([]);
  const [webhookDeliveries, setWebhookDeliveries] = useState<WebhookDelivery[]>([]);
  const [isLoadingEmails, setIsLoadingEmails] = useState(true);
  const [isLoadingWebhooks, setIsLoadingWebhooks] = useState(true);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    // Load email sends
    setIsLoadingEmails(true);
    try {
      const emailResponse = await api.getNotificationSends({
        notification_type: 'email',
        limit: 10,
      });
      setEmailSends(emailResponse.sends || []);
    } catch (err: any) {
      console.error('Failed to load email history:', err);
    } finally {
      setIsLoadingEmails(false);
    }

    // Load webhook deliveries
    setIsLoadingWebhooks(true);
    try {
      const webhookResponse = await api.getWebhookDeliveries({ limit: 10 });
      setWebhookDeliveries(webhookResponse.deliveries || []);
    } catch (err: any) {
      console.error('Failed to load webhook history:', err);
    } finally {
      setIsLoadingWebhooks(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const StatusBadge = ({ status }: { status: string }) => {
    switch (status) {
      case 'success':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[9px] font-mono uppercase tracking-wider border border-emerald-200">
            <CheckCircle2 className="h-3 w-3" />
            Success
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-red-50 text-red-700 text-[9px] font-mono uppercase tracking-wider border border-red-200">
            <XCircle className="h-3 w-3" />
            Failed
          </span>
        );
      case 'retrying':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-amber-50 text-amber-700 text-[9px] font-mono uppercase tracking-wider border border-amber-200">
            <Clock className="h-3 w-3" />
            Retrying
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-1.5 py-0.5 bg-zinc-50 text-zinc-600 text-[9px] font-mono uppercase tracking-wider border border-zinc-200">
            {status}
          </span>
        );
    }
  };

  return (
    <BrutalistCard>
      {/* Header */}
      <div className="p-4 border-b border-zinc-200">
        <p className="text-xs text-zinc-500">
          Recent email sends and webhook deliveries
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-zinc-200">
        <button
          onClick={() => setActiveTab('emails')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-xs font-mono transition-colors ${
            activeTab === 'emails'
              ? 'bg-zinc-900 text-white'
              : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50'
          }`}
        >
          <Mail className="h-4 w-4" />
          Emails
        </button>
        <button
          onClick={() => setActiveTab('webhooks')}
          className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 text-xs font-mono transition-colors ${
            activeTab === 'webhooks'
              ? 'bg-zinc-900 text-white'
              : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50'
          }`}
        >
          <Webhook className="h-4 w-4" />
          Webhooks
        </button>
      </div>

      {/* Content */}
      <div className="p-4">
        {activeTab === 'emails' ? (
          // Email Sends
          isLoadingEmails ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
            </div>
          ) : emailSends.length === 0 ? (
            <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
              <Mail className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
              <p className="text-xs text-zinc-500 font-mono">
                No email notifications sent yet
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {emailSends.map((send) => (
                <div
                  key={send.id}
                  className="p-3 border border-zinc-200 hover:border-zinc-300 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center shrink-0">
                      <Mail className="h-4 w-4 text-zinc-600" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs sm:text-sm font-mono text-zinc-900 break-all">{send.recipient}</p>
                      <p className="text-[10px] font-mono text-zinc-400 mt-0.5">{formatDate(send.created_at)}</p>
                      <div className="flex items-center gap-1.5 mt-2">
                        <StatusBadge status={send.status} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          // Webhook Deliveries
          isLoadingWebhooks ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
            </div>
          ) : webhookDeliveries.length === 0 ? (
            <div className="p-4 bg-zinc-50 border border-dashed border-zinc-300 text-center">
              <Webhook className="h-5 w-5 text-zinc-400 mx-auto mb-2" />
              <p className="text-xs text-zinc-500 font-mono">
                No webhook deliveries yet
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {webhookDeliveries.map((delivery) => (
                <div
                  key={delivery.id}
                  className="p-3 border border-zinc-200 hover:border-zinc-300 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="bg-zinc-100 w-8 h-8 flex items-center justify-center shrink-0">
                      <Webhook className="h-4 w-4 text-zinc-600" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs sm:text-sm font-mono text-zinc-900 break-all">{delivery.webhook_url}</p>
                      <p className="text-[10px] font-mono text-zinc-400 mt-0.5">{formatDate(delivery.created_at)}</p>
                      <div className="flex flex-wrap items-center gap-1.5 mt-2">
                        {delivery.http_status_code && (
                          <span className="px-1.5 py-0.5 bg-zinc-100 text-zinc-600 text-[9px] font-mono">
                            {delivery.http_status_code}
                          </span>
                        )}
                        <StatusBadge status={delivery.status} />
                      </div>

                      {/* Retry Info */}
                      {delivery.attempts > 1 && (
                        <p className="text-[10px] font-mono text-zinc-500 mt-2">
                          Attempt {delivery.attempts}
                          {delivery.next_retry_at && ` • Next retry: ${formatDate(delivery.next_retry_at)}`}
                        </p>
                      )}

                      {/* Error Message */}
                      {delivery.error_message && (
                        <div className="mt-2 p-2 bg-red-50 border border-red-200 text-red-700 text-[10px] font-mono break-all">
                          {delivery.error_message}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </BrutalistCard>
  );
};
