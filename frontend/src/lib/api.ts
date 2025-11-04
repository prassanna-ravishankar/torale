import type { Task, TaskExecution, User } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface ApiError {
  detail: string
}

class ApiClient {
  private tokenGetter: (() => Promise<string | null>) | null = null

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
    const response = await fetch(`${API_BASE_URL}/auth/sync-user`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  // Task endpoints
  async getTasks(): Promise<Task[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getTask(id: string): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${id}`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async createTask(task: Partial<Task>): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(task),
    })
    return this.handleResponse(response)
  }

  async updateTask(id: string, task: Partial<Task>): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${id}`, {
      method: 'PUT',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(task),
    })
    return this.handleResponse(response)
  }

  async deleteTask(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${id}`, {
      method: 'DELETE',
      headers: await this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to delete task: ${response.status}`)
    }
  }

  async executeTask(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${id}/execute`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`Failed to execute task: ${response.status}`)
    }
  }

  // Task execution endpoints
  async getTaskExecutions(taskId: string): Promise<TaskExecution[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${taskId}/executions`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }

  async getTaskNotifications(taskId: string): Promise<TaskExecution[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/tasks/${taskId}/notifications`, {
      headers: await this.getAuthHeaders(),
    })
    return this.handleResponse(response)
  }
}

export const api = new ApiClient()
export default api
