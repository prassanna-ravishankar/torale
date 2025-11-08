import type { Task, TaskExecution, TaskTemplate, User } from '@/types'

interface ApiError {
  detail: string
}

class ApiClient {
  private tokenGetter: (() => Promise<string | null>) | null = null

  // Read API URL from runtime config (evaluated at request time, not module load time)
  private get baseUrl(): string {
    return window.CONFIG?.apiUrl || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
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

  async createTask(task: Partial<Task>): Promise<Task> {
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

  async executeTask(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/tasks/${id}/execute`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to execute task: ${response.status}`)
    }
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

  async getTemporalWorkflows(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/admin/temporal/workflows`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getTemporalSchedules(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/admin/temporal/schedules`, {
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
}

export const api = new ApiClient()
export default api
