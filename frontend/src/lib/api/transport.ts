import { watchRssPath } from '@/lib/watchRoutes'

interface ApiErrorBody { detail: string }

export class ApiError extends Error {
  constructor(
    public readonly status: number | null,
    public readonly detail: string,
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

export type TokenGetter = (options?: { skipCache?: boolean }) => Promise<string | null>
export type ApiAuthMode = 'clerk' | 'noauth'

export interface ApiClientOptions {
  authMode: ApiAuthMode
  getToken?: TokenGetter
  fetchImpl?: typeof globalThis.fetch
}

export class ApiTransport {
  private readonly authMode: ApiAuthMode
  private readonly tokenGetter?: TokenGetter
  private readonly fetchImpl: typeof globalThis.fetch

  constructor({ authMode, getToken, fetchImpl }: ApiClientOptions) {
    this.authMode = authMode
    this.tokenGetter = getToken
    // Browser fetch is a host method and must retain its Window receiver.
    this.fetchImpl = fetchImpl ?? globalThis.fetch.bind(globalThis)
  }

  getBaseUrl(): string {
    return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  }

  buildPath(path: string, params?: Record<string, string | number | boolean | undefined>): string {
    if (!params) return path
    const searchParams = new URLSearchParams()
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) searchParams.set(key, String(value))
    }
    const query = searchParams.toString()
    return query ? `${path}?${query}` : path
  }

  buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): string {
    return `${this.getBaseUrl()}${this.buildPath(path, params)}`
  }

  getTaskRssUrl(taskId: string): string {
    return `${this.getBaseUrl()}${watchRssPath(taskId)}`
  }

  async request<T>(path: string, init: RequestInit = {}, authenticated = true): Promise<T> {
    const response = await this.fetchRequest(this.buildUrl(path), {
      ...init,
      headers: authenticated ? await this.getAuthHeaders(init.headers) : init.headers,
    })
    return this.handleResponse<T>(response)
  }

  async requestEmpty(path: string, init: RequestInit = {}): Promise<void> {
    const response = await this.fetchRequest(this.buildUrl(path), {
      ...init,
      headers: await this.getAuthHeaders(init.headers),
    })
    if (!response.ok) await this.handleResponse(response)
  }

  private async getAuthHeaders(headers?: HeadersInit): Promise<Headers> {
    const token = this.tokenGetter ? await this.tokenGetter() : null
    if (this.authMode === 'clerk' && !token) {
      throw new ApiError(401, 'Your session is not ready. Please sign in again.')
    }
    const result = new Headers(headers)
    if (!result.has('Content-Type')) result.set('Content-Type', 'application/json')
    if (token) result.set('Authorization', `Bearer ${token}`)
    return result
  }

  private async fetchRequest(input: RequestInfo | URL, init: RequestInit): Promise<Response> {
    const response = await this.fetchImpl(input, init)
    const headers = new Headers(init.headers)
    if (response.status !== 401 || !headers.has('Authorization') || !this.tokenGetter) return response

    const freshToken = await this.tokenGetter({ skipCache: true })
    if (!freshToken) return response
    headers.set('Authorization', `Bearer ${freshToken}`)
    return this.fetchImpl(input, { ...init, headers })
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error: ApiErrorBody = await response.json().catch(() => ({ detail: 'An error occurred' }))
      throw new ApiError(response.status, error.detail || `HTTP error! status: ${response.status}`)
    }
    return response.json()
  }
}
