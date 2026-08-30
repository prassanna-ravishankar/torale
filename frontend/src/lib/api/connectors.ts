import type { AvailableToolkit, UserConnection } from '@/types'
import type { ApiTransport } from './transport'

export const createConnectorsApi = (transport: ApiTransport) => ({
  getConnections: () => transport.request<UserConnection[]>('/api/v1/connectors'),
  getAvailableToolkits: () => transport.request<AvailableToolkit[]>('/api/v1/connectors/available'),
  getUserConnections: () => transport.request<UserConnection[]>('/api/v1/connectors'),
  connectToolkit: (toolkitSlug: string) =>
    transport.request<{ redirect_url: string | null }>(`/api/v1/connectors/${toolkitSlug}/connect`, { method: 'POST' }),
  disconnectToolkit: (toolkitSlug: string) =>
    transport.requestEmpty(`/api/v1/connectors/${toolkitSlug}`, { method: 'DELETE' }),
})

export type ConnectorsApi = ReturnType<typeof createConnectorsApi>
