import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Mail, Webhook, CheckCircle2, XCircle, Clock, ExternalLink } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import type { WebhookDelivery, NotificationSend } from '@/types';

export const NotificationHistorySection: React.FC = () => {
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return (
          <Badge variant="secondary" className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            Success
          </Badge>
        );
      case 'failed':
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            Failed
          </Badge>
        );
      case 'retrying':
        return (
          <Badge variant="outline" className="gap-1">
            <Clock className="h-3 w-3" />
            Retrying
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Notification History</CardTitle>
        <CardDescription>Recent email sends and webhook deliveries</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="emails" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="emails" className="gap-2">
              <Mail className="h-4 w-4" />
              Email Sends
            </TabsTrigger>
            <TabsTrigger value="webhooks" className="gap-2">
              <Webhook className="h-4 w-4" />
              Webhook Deliveries
            </TabsTrigger>
          </TabsList>

          {/* Email Sends Tab */}
          <TabsContent value="emails" className="space-y-4">
            {isLoadingEmails ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : emailSends.length === 0 ? (
              <Alert>
                <Mail className="h-4 w-4" />
                <AlertDescription>
                  No email notifications sent yet. Email notifications will appear here when task
                  conditions are met.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-2">
                {emailSends.map((send) => (
                  <div
                    key={send.id}
                    className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <Mail className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                      <div className="flex flex-col min-w-0 flex-1">
                        <span className="font-medium truncate">{send.recipient}</span>
                        <span className="text-sm text-muted-foreground">
                          {formatDate(send.created_at)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {getStatusBadge(send.status)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Webhook Deliveries Tab */}
          <TabsContent value="webhooks" className="space-y-4">
            {isLoadingWebhooks ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : webhookDeliveries.length === 0 ? (
              <Alert>
                <Webhook className="h-4 w-4" />
                <AlertDescription>
                  No webhook deliveries yet. Webhook notifications will appear here when task
                  conditions are met.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-2">
                {webhookDeliveries.map((delivery) => (
                  <div
                    key={delivery.id}
                    className="rounded-lg border p-4 hover:bg-accent/50 transition-colors space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        <Webhook className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        <div className="flex flex-col min-w-0 flex-1">
                          <span className="font-medium truncate">{delivery.webhook_url}</span>
                          <span className="text-sm text-muted-foreground">
                            {formatDate(delivery.created_at)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {delivery.http_status_code && (
                          <Badge variant="outline">{delivery.http_status_code}</Badge>
                        )}
                        {getStatusBadge(delivery.status)}
                      </div>
                    </div>

                    {/* Retry Info */}
                    {delivery.attempts > 1 && (
                      <div className="text-sm text-muted-foreground pl-7">
                        Attempt {delivery.attempts}
                        {delivery.next_retry_at && (
                          <span> • Next retry: {formatDate(delivery.next_retry_at)}</span>
                        )}
                      </div>
                    )}

                    {/* Error Message */}
                    {delivery.error_message && (
                      <Alert variant="destructive" className="mt-2">
                        <XCircle className="h-4 w-4" />
                        <AlertDescription className="text-xs">
                          {delivery.error_message}
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
