import type { NotificationSend, WebhookConfig, WebhookDelivery } from '@/types'
import type { ApiTransport } from './transport'

export const createNotificationsApi = (transport: ApiTransport) => ({
  sendVerificationCode: (email: string) =>
    transport.request<{ message: string; expires_at: string }>('/api/v1/email-verification/send', {
      method: 'POST', body: JSON.stringify({ email }),
    }),
  verifyEmailCode: (email: string, code: string) =>
    transport.request<{ message: string; email: string }>('/api/v1/email-verification/verify', {
      method: 'POST', body: JSON.stringify({ email, code }),
    }),
  getVerifiedEmails: () =>
    transport.request<{ verified_emails: string[] }>('/api/v1/email-verification/verified-emails'),
  removeVerifiedEmail: (email: string) =>
    transport.request<{ message: string }>(`/api/v1/email-verification/verified-emails/${encodeURIComponent(email)}`, {
      method: 'DELETE',
    }),
  getWebhookConfig: () => transport.request<WebhookConfig>('/api/v1/webhooks/config'),
  updateWebhookConfig: (url: string, enabled = true) => transport.request<WebhookConfig>('/api/v1/webhooks/config', {
    method: 'PUT', body: JSON.stringify({ webhook_url: url, enabled }),
  }),
  testWebhook: (url: string, secret: string) =>
    transport.request<{ success: boolean; message: string }>('/api/v1/webhooks/test', {
      method: 'POST', body: JSON.stringify({ webhook_url: url, webhook_secret: secret }),
    }),
  getWebhookDeliveries: (params?: { task_id?: string; limit?: number; offset?: number }) =>
    transport.request<{ deliveries: WebhookDelivery[]; total: number }>(path(transport, '/api/v1/webhooks/deliveries', params)),
  getNotificationSends: (params?: {
    task_id?: string
    notification_type?: 'email' | 'webhook'
    limit?: number
    offset?: number
  }) => transport.request<{ sends: NotificationSend[]; total: number }>(
    path(transport, '/api/v1/notifications/sends', params),
  ),
})

const path = (
  transport: ApiTransport,
  pathname: string,
  params?: Record<string, string | number | boolean | undefined>,
) => transport.buildPath(pathname, params)

export type NotificationsApi = ReturnType<typeof createNotificationsApi>
