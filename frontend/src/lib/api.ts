import type {
  AvailableToolkit,
  Task,
  TaskCreatePayload,
  TaskExecution,
  TaskTemplate,
  UserConnection,
  WebhookConfig,
  WebhookDelivery,
  NotificationSend,
  ApiKey,
  CreateApiKeyResponse,
  FeedExecution,
} from '@/types'
import { watchRssPath } from '@/lib/watchRoutes'

interface ApiErrorBody {
  detail: string
}

export interface UserRead {
  id: string
  clerk_user_id: string
  email: string
  first_name: string | null
  username: string | null
  is_active: boolean
  has_seen_welcome: boolean
  created_at: string
}

export interface SyncUserResponse {
  user: UserRead
  created: boolean
}

export class ApiError extends Error {
  constructor(
    public readonly status: number | null,
    public readonly detail: string
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

export type TokenGetter = (options?: { skipCache?: boolean }) => Promise<string | null>
export type ApiAuthMode = 'clerk' | 'noauth'

interface ApiClientOptions {
  authMode: ApiAuthMode
  getToken?: TokenGetter
  fetchImpl?: typeof globalThis.fetch
}

export class ApiClient {
  private readonly authMode: ApiAuthMode
  private readonly tokenGetter?: TokenGetter
  private readonly fetchImpl: typeof globalThis.fetch

  constructor({ authMode, getToken, fetchImpl = globalThis.fetch }: ApiClientOptions) {
    this.authMode = authMode
    this.tokenGetter = getToken
    this.fetchImpl = fetchImpl
  }

  // Read API URL from build-time env var
  private get baseUrl(): string {
    return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  }

  // Public getter for API base URL (for use in components that need direct API URL access)
  getBaseUrl(): string {
    return this.baseUrl
  }

  private buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
    const url = `${this.baseUrl}${path}`
    if (!params) return url
    const searchParams = new URLSearchParams()
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        searchParams.set(key, String(value))
      }
    }
    const qs = searchParams.toString()
    return qs ? `${url}?${qs}` : url
  }

  /** Build the RSS feed URL for a public task. */
  getTaskRssUrl(taskId: string): string {
    return `${this.baseUrl}${watchRssPath(taskId)}`
  }

  private async getAuthHeaders(): Promise<HeadersInit> {
    const token = this.tokenGetter ? await this.tokenGetter() : null
    if (this.authMode === 'clerk' && !token) {
      throw new ApiError(401, 'Your session is not ready. Please sign in again.')
    }

    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }
  }

  private async fetchRequest(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
    const response = await this.fetchImpl(input, init)
    const headers = new Headers(init.headers)
    if (response.status !== 401 || !headers.has('Authorization') || !this.tokenGetter) {
      return response
    }

    const freshToken = await this.tokenGetter({ skipCache: true })
    if (!freshToken) return response

    headers.set('Authorization', `Bearer ${freshToken}`)
    return this.fetchImpl(input, { ...init, headers })
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiErrorBody = await response.json().catch(() => ({
        detail: 'An error occurred',
      }))
      throw new ApiError(response.status, error.detail || `HTTP error! status: ${response.status}`)
    }
    return response.json()
  }

  private async handleEmptyResponse(response: Response): Promise<void> {
    if (!response.ok) await this.handleResponse(response)
  }

  // Sync user with backend on first login
  async syncUser(): Promise<SyncUserResponse> {
    const response = await this.fetchRequest(`${this.baseUrl}/auth/sync-user`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getCurrentUser(): Promise<UserRead> {
    const response = await this.fetchRequest(`${this.baseUrl}/auth/me`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async markWelcomeSeen(): Promise<void> {
    const response = await this.fetchRequest(`${this.baseUrl}/auth/mark-welcome-seen`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Task endpoints
  async getTasks(): Promise<Task[]> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/tasks/`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getTask(id: string): Promise<Task> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/tasks/${id}`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async createTask(task: TaskCreatePayload): Promise<Task> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/tasks/`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(task),
    })
    return this.handleResponse(response)
  }

  async updateTask(id: string, task: Partial<Task>): Promise<Task> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/tasks/${id}`, {
      method: 'PUT',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(task),
    })
    return this.handleResponse(response)
  }

  async deleteTask(id: string): Promise<void> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/tasks/${id}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    return this.handleEmptyResponse(response)
  }

  async executeTask(id: string, suppressNotifications: boolean = false): Promise<TaskExecution> {
    const url = this.buildUrl(`/api/v1/tasks/${id}/execute`, {
      suppress_notifications: suppressNotifications || undefined,
    })

    const response = await this.fetchRequest(url, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Task execution endpoints
  async getTaskExecutions(taskId: string): Promise<TaskExecution[]> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/tasks/${taskId}/executions`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getTaskNotifications(taskId: string): Promise<TaskExecution[]> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/tasks/${taskId}/notifications`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Template endpoints
  async getTemplates(category?: string): Promise<TaskTemplate[]> {
    const url = this.buildUrl('/api/v1/templates/', { category })
    const response = await this.fetchRequest(url)
    return this.handleResponse(response)
  }

  async getTemplate(id: string): Promise<TaskTemplate> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/templates/${id}`)
    return this.handleResponse(response)
  }

  // Admin endpoints (callers provide expected response type via generic parameter)
  async getAdminStats<T = Record<string, unknown>>(): Promise<T> {
    const response = await this.fetchRequest(`${this.baseUrl}/admin/stats`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async getAdminQueries<T = Record<string, unknown>>(params?: { limit?: number; active_only?: boolean }): Promise<T> {
    const url = this.buildUrl('/admin/queries', {
      limit: params?.limit,
      active_only: params?.active_only,
    })
    const response = await this.fetchRequest(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async getAdminExecutions<T = Record<string, unknown>>(params?: { limit?: number; status?: string; task_id?: string }): Promise<T> {
    const url = this.buildUrl('/admin/executions', {
      limit: params?.limit,
      status: params?.status,
      task_id: params?.task_id,
    })
    const response = await this.fetchRequest(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async getAdminErrors<T = Record<string, unknown>>(params?: { limit?: number }): Promise<T> {
    const url = this.buildUrl('/admin/errors', { limit: params?.limit })
    const response = await this.fetchRequest(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async getAdminUsers<T = Record<string, unknown>>(): Promise<T> {
    const response = await this.fetchRequest(`${this.baseUrl}/admin/users`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async deactivateUser<T = Record<string, unknown>>(userId: string): Promise<T> {
    const response = await this.fetchRequest(`${this.baseUrl}/admin/users/${userId}/deactivate`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async updateUserRole(userId: string, role: string | null): Promise<{ status: string; user_id: string; role: string | null }> {
    const response = await this.fetchRequest(`${this.baseUrl}/admin/users/${userId}/role`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ role }),
    })
    return this.handleResponse(response)
  }

  async bulkUpdateUserRoles(userIds: string[], role: string | null): Promise<{ updated: number; failed: number; errors: unknown[] }> {
    const response = await this.fetchRequest(`${this.baseUrl}/admin/users/roles`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ user_ids: userIds, role }),
    })
    return this.handleResponse(response)
  }

  async adminExecuteTask(
    taskId: string,
    suppressNotifications: boolean = false
  ): Promise<{ id: string; task_id: string; status: string; message: string }> {
    const url = this.buildUrl(`/admin/tasks/${taskId}/execute`, {
      suppress_notifications: suppressNotifications,
    })
    const response = await this.fetchRequest(url, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  /**
   * Update task state (admin only).
   *
   * Note: While the API supports 'completed', the admin UI only exposes
   * pause/resume functionality ('active' | 'paused'). The 'completed' state
   * is reserved for future features or API-only operations.
   */
  async adminUpdateTaskState(
    taskId: string,
    state: 'active' | 'paused' | 'completed'
  ): Promise<{ id: string; state: string; previous_state: string; message: string }> {
    const response = await this.fetchRequest(`${this.baseUrl}/admin/tasks/${taskId}/state`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ state }),
    })
    return this.handleResponse(response)
  }

  async adminResetTask(
    taskId: string,
    days: number = 1
  ): Promise<{ status: string; task_id: string; executions_deleted: number; days: number }> {
    const url = this.buildUrl(`/admin/tasks/${taskId}/reset`, { days })
    const response = await this.fetchRequest(url, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Waitlist endpoints
  async getWaitlist<T = Record<string, unknown>>(statusFilter?: string): Promise<T> {
    const url = this.buildUrl('/admin/waitlist', { status_filter: statusFilter })
    const response = await this.fetchRequest(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async getWaitlistStats<T = Record<string, unknown>>(): Promise<T> {
    const response = await this.fetchRequest(`${this.baseUrl}/admin/waitlist/stats`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async updateWaitlistEntry<T = Record<string, unknown>>(entryId: string, data: { status?: string; notes?: string }): Promise<T> {
    const response = await this.fetchRequest(`${this.baseUrl}/admin/waitlist/${entryId}`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    return this.handleResponse<T>(response)
  }

  async deleteWaitlistEntry(entryId: string): Promise<void> {
    const response = await this.fetchRequest(`${this.baseUrl}/admin/waitlist/${entryId}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    return this.handleEmptyResponse(response)
  }

  // Email Verification endpoints
  async sendVerificationCode(email: string): Promise<{ message: string; expires_at: string }> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/email-verification/send`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ email }),
    })
    return this.handleResponse(response)
  }

  async verifyEmailCode(email: string, code: string): Promise<{ message: string; email: string }> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/email-verification/verify`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ email, code }),
    })
    return this.handleResponse(response)
  }

  async getVerifiedEmails(): Promise<{ verified_emails: string[] }> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/email-verification/verified-emails`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async removeVerifiedEmail(email: string): Promise<{ message: string }> {
    const encodedEmail = encodeURIComponent(email)
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/email-verification/verified-emails/${encodedEmail}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Webhook endpoints
  async getWebhookConfig(): Promise<WebhookConfig> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/webhooks/config`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async updateWebhookConfig(url: string, enabled: boolean = true): Promise<WebhookConfig> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/webhooks/config`, {
      method: 'PUT',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ webhook_url: url, enabled }),
    })
    return this.handleResponse(response)
  }

  async testWebhook(url: string, secret: string): Promise<{ success: boolean; message: string }> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/webhooks/test`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ webhook_url: url, webhook_secret: secret }),
    })
    return this.handleResponse(response)
  }

  async getWebhookDeliveries(params?: {
    task_id?: string
    limit?: number
    offset?: number
  }): Promise<{ deliveries: WebhookDelivery[]; total: number }> {
    const url = this.buildUrl('/api/v1/webhooks/deliveries', {
      task_id: params?.task_id,
      limit: params?.limit,
      offset: params?.offset,
    })
    const response = await this.fetchRequest(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Notification history endpoints
  async getNotificationSends(params?: {
    task_id?: string
    notification_type?: 'email' | 'webhook'
    limit?: number
    offset?: number
  }): Promise<{ sends: NotificationSend[]; total: number }> {
    const url = this.buildUrl('/api/v1/notifications/sends', {
      task_id: params?.task_id,
      notification_type: params?.notification_type,
      limit: params?.limit,
      offset: params?.offset,
    })
    const response = await this.fetchRequest(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // API Key Management endpoints
  async createApiKey(name: string): Promise<CreateApiKeyResponse> {
    const response = await this.fetchRequest(`${this.baseUrl}/auth/api-keys`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ name }),
    })
    return this.handleResponse(response)
  }

  async getApiKeys(): Promise<ApiKey[]> {
    const response = await this.fetchRequest(`${this.baseUrl}/auth/api-keys`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async revokeApiKey(keyId: string): Promise<{ status: string }> {
    const response = await this.fetchRequest(`${this.baseUrl}/auth/api-keys/${keyId}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Task visibility endpoints
  async updateTaskVisibility(
    taskId: string,
    isPublic: boolean
  ): Promise<{ is_public: boolean }> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/tasks/${taskId}/visibility`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ is_public: isPublic }),
    })
    return this.handleResponse(response)
  }

  // Task forking
  async forkTask(taskId: string, name?: string): Promise<Task> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/tasks/${taskId}/fork`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ name }),
    })
    return this.handleResponse(response)
  }

  // Connector endpoints
  async getConnections(): Promise<UserConnection[]> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/connectors`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Feed endpoints
  async getFeed(limit: number = 50): Promise<FeedExecution[]> {
    const url = this.buildUrl('/api/v1/tasks/feed', { limit })
    const response = await this.fetchRequest(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Connector endpoints
  async getAvailableToolkits(): Promise<AvailableToolkit[]> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/connectors/available`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getUserConnections(): Promise<UserConnection[]> {
    const response = await this.fetchRequest(`${this.baseUrl}/api/v1/connectors`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async connectToolkit(toolkitSlug: string): Promise<{ redirect_url: string | null }> {
    const response = await this.fetchRequest(
      `${this.baseUrl}/api/v1/connectors/${toolkitSlug}/connect`,
      {
        method: 'POST',
        headers: await this.getAuthHeaders(),
      }
    )
    return this.handleResponse(response)
  }

  async disconnectToolkit(toolkitSlug: string): Promise<void> {
    const response = await this.fetchRequest(
      `${this.baseUrl}/api/v1/connectors/${toolkitSlug}`,
      {
        method: 'DELETE',
        headers: await this.getAuthHeaders(),
      }
    )
    return this.handleEmptyResponse(response)
  }
}

export const createApiClient = (options: ApiClientOptions): ApiClient => new ApiClient(options)
