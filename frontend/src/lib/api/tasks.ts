import type { FeedExecution, Task, TaskCreatePayload, TaskExecution, TaskTemplate } from '@/types'
import type { ApiTransport } from './transport'

export const createTasksApi = (transport: ApiTransport) => ({
  getTasks: () => transport.request<Task[]>('/api/v1/tasks/'),
  getTask: (id: string) => transport.request<Task>(`/api/v1/tasks/${id}`),
  createTask: (task: TaskCreatePayload) => transport.request<Task>('/api/v1/tasks/', {
    method: 'POST', body: JSON.stringify(task),
  }),
  updateTask: (id: string, task: Partial<Task>) => transport.request<Task>(`/api/v1/tasks/${id}`, {
    method: 'PUT', body: JSON.stringify(task),
  }),
  deleteTask: (id: string) => transport.requestEmpty(`/api/v1/tasks/${id}`, { method: 'DELETE' }),
  executeTask: (id: string, suppressNotifications = false) => transport.request<TaskExecution>(
    transport.buildPath(`/api/v1/tasks/${id}/execute`, {
      suppress_notifications: suppressNotifications || undefined,
    }),
    { method: 'POST' },
  ),
  getTaskExecutions: (taskId: string) => transport.request<TaskExecution[]>(`/api/v1/tasks/${taskId}/executions`),
  getTaskNotifications: (taskId: string) => transport.request<TaskExecution[]>(`/api/v1/tasks/${taskId}/notifications`),
  getTemplates: (category?: string) => transport.request<TaskTemplate[]>(
    transport.buildPath('/api/v1/templates/', { category }), {}, false,
  ),
  getTemplate: (id: string) => transport.request<TaskTemplate>(`/api/v1/templates/${id}`, {}, false),
  updateTaskVisibility: (taskId: string, isPublic: boolean) => transport.request<{ is_public: boolean }>(
    `/api/v1/tasks/${taskId}/visibility`, { method: 'PATCH', body: JSON.stringify({ is_public: isPublic }) },
  ),
  forkTask: (taskId: string, name?: string) => transport.request<Task>(`/api/v1/tasks/${taskId}/fork`, {
    method: 'POST', body: JSON.stringify({ name }),
  }),
  getFeed: (limit = 50) => transport.request<FeedExecution[]>(`/api/v1/tasks/feed?limit=${limit}`),
})

export type TasksApi = ReturnType<typeof createTasksApi>
