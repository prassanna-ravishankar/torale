import type { ApiTransport } from './transport'

export const createAdminApi = (transport: ApiTransport) => ({
  getAdminStats: <T = Record<string, unknown>>() => transport.request<T>('/admin/stats'),
  getAdminQueries: <T = Record<string, unknown>>(params?: { limit?: number; active_only?: boolean }) =>
    transport.request<T>(path(transport, '/admin/queries', params)),
  getAdminExecutions: <T = Record<string, unknown>>(params?: { limit?: number; status?: string; task_id?: string }) =>
    transport.request<T>(path(transport, '/admin/executions', params)),
  getAdminErrors: <T = Record<string, unknown>>(params?: { limit?: number }) =>
    transport.request<T>(path(transport, '/admin/errors', params)),
  getAdminUsers: <T = Record<string, unknown>>() => transport.request<T>('/admin/users'),
  deactivateUser: <T = Record<string, unknown>>(userId: string) =>
    transport.request<T>(`/admin/users/${userId}/deactivate`, { method: 'PATCH' }),
  updateUserRole: (userId: string, role: string | null) =>
    transport.request<{ status: string; user_id: string; role: string | null }>(`/admin/users/${userId}/role`, {
      method: 'PATCH', body: JSON.stringify({ role }),
    }),
  bulkUpdateUserRoles: (userIds: string[], role: string | null) =>
    transport.request<{ updated: number; failed: number; errors: unknown[] }>('/admin/users/roles', {
      method: 'PATCH', body: JSON.stringify({ user_ids: userIds, role }),
    }),
  adminExecuteTask: (taskId: string, suppressNotifications = false) =>
    transport.request<{ id: string; task_id: string; status: string; message: string }>(
      path(transport, `/admin/tasks/${taskId}/execute`, { suppress_notifications: suppressNotifications }),
      { method: 'POST' },
    ),
  adminUpdateTaskState: (taskId: string, state: 'active' | 'paused' | 'completed') =>
    transport.request<{ id: string; state: string; previous_state: string; message: string }>(
      `/admin/tasks/${taskId}/state`, { method: 'PATCH', body: JSON.stringify({ state }) },
    ),
  adminResetTask: (taskId: string, days = 1) =>
    transport.request<{ status: string; task_id: string; executions_deleted: number; days: number }>(
      path(transport, `/admin/tasks/${taskId}/reset`, { days }), { method: 'DELETE' },
    ),
  getWaitlist: <T = Record<string, unknown>>(statusFilter?: string) =>
    transport.request<T>(path(transport, '/admin/waitlist', { status_filter: statusFilter })),
  getWaitlistStats: <T = Record<string, unknown>>() => transport.request<T>('/admin/waitlist/stats'),
  updateWaitlistEntry: <T = Record<string, unknown>>(entryId: string, data: { status?: string; notes?: string }) =>
    transport.request<T>(`/admin/waitlist/${entryId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteWaitlistEntry: (entryId: string) => transport.requestEmpty(`/admin/waitlist/${entryId}`, { method: 'DELETE' }),
})

const path = (
  transport: ApiTransport,
  pathname: string,
  params?: Record<string, string | number | boolean | undefined>,
) => transport.buildPath(pathname, params)

export type AdminApi = ReturnType<typeof createAdminApi>
