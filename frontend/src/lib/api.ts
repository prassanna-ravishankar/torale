import type {
  Task,
  TaskCreatePayload,
  TaskExecution,
  TaskTemplate,
  User,
  UserWithNotifications,
  WebhookConfig,
  WebhookDelivery,
  NotificationSend,
  ApiKey,
  CreateApiKeyResponse,
} from '@/types'

interface ApiError {
  detail: string
}

class ApiClient {
  private tokenGetter: (() => Promise<string | null>) | null = null

  // Read API URL from runtime config (evaluated at request time, not module load time)
  private get baseUrl(): string {
    return window.CONFIG?.apiUrl || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  }

  // Public getter for API base URL (for use in components that need direct API URL access)
  getBaseUrl(): string {
    return this.baseUrl
  }

  // Set the token getter function (called from components with Clerk's getToken)
  setTokenGetter(getter: () => Promise<string | null>) {
    this.tokenGetter = getter
  }

  private async getAuthHeaders(): Promise<HeadersInit> {
    let token: string | null = null

    if (this.tokenGetter) {
      token = await this.tokenGetter()
    }

    return {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: 'An error occurred',
      }))
      throw new Error(error.detail || `HTTP error! status: ${response.status}`)
    }
    return response.json()
  }

  // Sync user with backend on first login
  async syncUser(): Promise<User> {
    const response = await fetch(`${this.baseUrl}/auth/sync-user`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${this.baseUrl}/auth/me`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Task endpoints
  async getTasks(): Promise<Task[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getTask(id: string): Promise<Task> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/${id}`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async createTask(task: TaskCreatePayload): Promise<Task> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(task),
    })
    return this.handleResponse(response)
  }

  async updateTask(id: string, task: Partial<Task>): Promise<Task> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/${id}`, {
      method: 'PUT',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(task),
    })
    return this.handleResponse(response)
  }

  async deleteTask(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/${id}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to delete task: ${response.status}`)
    }
  }

  async executeTask(id: string, suppressNotifications: boolean = false): Promise<TaskExecution> {
    const url = suppressNotifications
      ? `${this.baseUrl}/api/v1/tasks/${id}/execute?suppress_notifications=true`
      : `${this.baseUrl}/api/v1/tasks/${id}/execute`

    const response = await fetch(url, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Task execution endpoints
  async getTaskExecutions(taskId: string): Promise<TaskExecution[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/${taskId}/executions`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getTaskNotifications(taskId: string): Promise<TaskExecution[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/${taskId}/notifications`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Template endpoints
  async getTemplates(category?: string): Promise<TaskTemplate[]> {
    const url = category
      ? `${this.baseUrl}/api/v1/templates/?category=${encodeURIComponent(category)}`
      : `${this.baseUrl}/api/v1/templates/`
    const response = await fetch(url)
    return this.handleResponse(response)
  }

  async getTemplate(id: string): Promise<TaskTemplate> {
    const response = await fetch(`${this.baseUrl}/api/v1/templates/${id}`)
    return this.handleResponse(response)
  }

  // Admin endpoints
  async getAdminStats(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/admin/stats`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getAdminQueries(params?: { limit?: number; active_only?: boolean }): Promise<any> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.set('limit', params.limit.toString())
    if (params?.active_only) queryParams.set('active_only', 'true')

    const url = `${this.baseUrl}/admin/queries${queryParams.toString() ? `?${queryParams}` : ''}`
    const response = await fetch(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getAdminExecutions(params?: { limit?: number; status?: string; task_id?: string }): Promise<any> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.set('limit', params.limit.toString())
    if (params?.status) queryParams.set('status', params.status)
    if (params?.task_id) queryParams.set('task_id', params.task_id)

    const url = `${this.baseUrl}/admin/executions${queryParams.toString() ? `?${queryParams}` : ''}`
    const response = await fetch(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getSchedulerJobs(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/admin/scheduler/jobs`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getAdminErrors(params?: { limit?: number }): Promise<any> {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.set('limit', params.limit.toString())

    const url = `${this.baseUrl}/admin/errors${queryParams.toString() ? `?${queryParams}` : ''}`
    const response = await fetch(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getAdminUsers(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/admin/users`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async deactivateUser(userId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/admin/users/${userId}/deactivate`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async updateUserRole(userId: string, role: string | null): Promise<{ status: string; user_id: string; role: string | null }> {
    const response = await fetch(`${this.baseUrl}/admin/users/${userId}/role`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ role }),
    })
    return this.handleResponse(response)
  }

  async bulkUpdateUserRoles(userIds: string[], role: string | null): Promise<{ updated: number; failed: number; errors: any[] }> {
    const response = await fetch(`${this.baseUrl}/admin/users/roles`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ user_ids: userIds, role }),
    })
    return this.handleResponse(response)
  }

  // Waitlist endpoints
  async getWaitlist(statusFilter?: string): Promise<any> {
    const url = statusFilter
      ? `${this.baseUrl}/admin/waitlist?status_filter=${statusFilter}`
      : `${this.baseUrl}/admin/waitlist`
    const response = await fetch(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getWaitlistStats(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/admin/waitlist/stats`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async updateWaitlistEntry(entryId: string, data: { status?: string; notes?: string }): Promise<any> {
    const response = await fetch(`${this.baseUrl}/admin/waitlist/${entryId}`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(data),
    })
    return this.handleResponse(response)
  }

  async deleteWaitlistEntry(entryId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/admin/waitlist/${entryId}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to delete waitlist entry: ${response.status}`)
    }
  }

  // Email Verification endpoints
  async sendVerificationCode(email: string): Promise<{ message: string; expires_at: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/email-verification/send`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ email }),
    })
    return this.handleResponse(response)
  }

  async verifyEmailCode(email: string, code: string): Promise<{ message: string; email: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/email-verification/verify`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ email, code }),
    })
    return this.handleResponse(response)
  }

  async getVerifiedEmails(): Promise<{ verified_emails: string[] }> {
    const response = await fetch(`${this.baseUrl}/api/v1/email-verification/verified-emails`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async removeVerifiedEmail(email: string): Promise<{ message: string }> {
    const encodedEmail = encodeURIComponent(email)
    const response = await fetch(`${this.baseUrl}/api/v1/email-verification/verified-emails/${encodedEmail}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Webhook endpoints
  async getWebhookConfig(): Promise<WebhookConfig> {
    const response = await fetch(`${this.baseUrl}/api/v1/webhooks/config`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async updateWebhookConfig(url: string, enabled: boolean = true): Promise<WebhookConfig> {
    const response = await fetch(`${this.baseUrl}/api/v1/webhooks/config`, {
      method: 'PUT',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ webhook_url: url, enabled }),
    })
    return this.handleResponse(response)
  }

  async testWebhook(url: string, secret: string): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/api/v1/webhooks/test`, {
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
    const queryParams = new URLSearchParams()
    if (params?.task_id) queryParams.set('task_id', params.task_id)
    if (params?.limit) queryParams.set('limit', params.limit.toString())
    if (params?.offset) queryParams.set('offset', params.offset.toString())

    const url = `${this.baseUrl}/api/v1/webhooks/deliveries${queryParams.toString() ? `?${queryParams}` : ''}`
    const response = await fetch(url, {
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
    const queryParams = new URLSearchParams()
    if (params?.task_id) queryParams.set('task_id', params.task_id)
    if (params?.notification_type) queryParams.set('notification_type', params.notification_type)
    if (params?.limit) queryParams.set('limit', params.limit.toString())
    if (params?.offset) queryParams.set('offset', params.offset.toString())

    const url = `${this.baseUrl}/api/v1/notifications/sends${queryParams.toString() ? `?${queryParams}` : ''}`
    const response = await fetch(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Get user with notification settings
  async getUserWithNotifications(): Promise<UserWithNotifications> {
    const response = await fetch(`${this.baseUrl}/auth/me`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // API Key Management endpoints
  async createApiKey(name: string): Promise<CreateApiKeyResponse> {
    const response = await fetch(`${this.baseUrl}/auth/api-keys`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ name }),
    })
    return this.handleResponse(response)
  }

  async getApiKeys(): Promise<ApiKey[]> {
    const response = await fetch(`${this.baseUrl}/auth/api-keys`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async revokeApiKey(keyId: string): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/auth/api-keys/${keyId}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Username endpoints
  async checkUsernameAvailability(username: string): Promise<{ available: boolean; error: string | null }> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/users/username/available?username=${encodeURIComponent(username)}`,
      {
        headers: await this.getAuthHeaders(),
      }
    )
    return this.handleResponse(response)
  }

  async setUsername(username: string): Promise<{ username: string; updated: boolean }> {
    const response = await fetch(`${this.baseUrl}/api/v1/users/me/username`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ username }),
    })
    return this.handleResponse(response)
  }

  // Task visibility endpoints
  async updateTaskVisibility(
    taskId: string,
    isPublic: boolean
  ): Promise<{ is_public: boolean; slug: string | null; username_required: boolean }> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/${taskId}/visibility`, {
      method: 'PATCH',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ is_public: isPublic }),
    })
    return this.handleResponse(response)
  }

  // Task forking
  async forkTask(taskId: string, name?: string): Promise<Task> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/${taskId}/fork`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify({ name }),
    })
    return this.handleResponse(response)
  }

  // Public task discovery
  async getPublicTasks(params?: {
    offset?: number
    limit?: number
    sort_by?: 'recent' | 'popular'
  }): Promise<{ tasks: Task[]; total: number; offset: number; limit: number }> {
    const queryParams = new URLSearchParams()
    if (params?.offset !== undefined) queryParams.set('offset', params.offset.toString())
    if (params?.limit) queryParams.set('limit', params.limit.toString())
    if (params?.sort_by) queryParams.set('sort_by', params.sort_by)

    const url = `${this.baseUrl}/api/v1/public/tasks${queryParams.toString() ? `?${queryParams}` : ''}`
    const response = await fetch(url, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getPublicTaskByVanityUrl(username: string, slug: string): Promise<Task> {
    const response = await fetch(`${this.baseUrl}/api/v1/public/tasks/${username}/${slug}`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getPublicTaskById(taskId: string): Promise<Task> {
    const response = await fetch(`${this.baseUrl}/api/v1/public/tasks/id/${taskId}`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }
}

export const api = new ApiClient()
export default api
