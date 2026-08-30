import { createAdminApi, type AdminApi } from './api/admin'
import { createAuthApi, type AuthApi } from './api/auth'
import { createConnectorsApi, type ConnectorsApi } from './api/connectors'
import { createNotificationsApi, type NotificationsApi } from './api/notifications'
import { createTasksApi, type TasksApi } from './api/tasks'
import {
  ApiError,
  ApiTransport,
  type ApiClientOptions,
  type ApiAuthMode,
  type TokenGetter,
} from './api/transport'

export { ApiError }
export type { ApiAuthMode, ApiClientOptions, TokenGetter }
export type { SyncUserResponse, UserRead } from './api/auth'

/** Stable facade: endpoint ownership is split without complicating usage sites. */
export type ApiClient = ApiClientFacade & AuthApi & TasksApi & AdminApi & NotificationsApi & ConnectorsApi

class ApiClientFacade {
  private readonly transport: ApiTransport

  constructor(transport: ApiTransport) {
    this.transport = transport
  }

  getBaseUrl(): string {
    return this.transport.getBaseUrl()
  }

  getTaskRssUrl(taskId: string): string {
    return this.transport.getTaskRssUrl(taskId)
  }
}

export const createApiClient = (options: ApiClientOptions): ApiClient => {
  const transport = new ApiTransport(options)
  const facade = new ApiClientFacade(transport)
  return Object.assign(
    facade,
    createAuthApi(transport),
    createTasksApi(transport),
    createAdminApi(transport),
    createNotificationsApi(transport),
    createConnectorsApi(transport),
  )
}
