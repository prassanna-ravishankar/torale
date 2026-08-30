import { describe, expect, it, vi } from 'vitest'

import { ApiError, createApiClient } from './api'

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })

describe('ApiClient authentication', () => {
  it('does not send an authenticated request until Clerk returns a token', async () => {
    const fetchImpl = vi.fn()
    const client = createApiClient({
      authMode: 'clerk',
      getToken: vi.fn().mockResolvedValue(null),
      fetchImpl,
    })

    await expect(client.getTask('watch-id')).rejects.toMatchObject({ status: 401 })
    expect(fetchImpl).not.toHaveBeenCalled()
  })

  it('retries one backend 401 with a fresh Clerk token', async () => {
    const getToken = vi.fn()
      .mockResolvedValueOnce('cached-token')
      .mockResolvedValueOnce('fresh-token')
    const fetchImpl = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(jsonResponse({ id: 'watch-id' }))
    const client = createApiClient({ authMode: 'clerk', getToken, fetchImpl })

    await expect(client.getTask('watch-id')).resolves.toMatchObject({ id: 'watch-id' })
    expect(getToken).toHaveBeenNthCalledWith(2, { skipCache: true })
    expect(new Headers(fetchImpl.mock.calls[1][1]?.headers).get('Authorization')).toBe('Bearer fresh-token')
    expect(fetchImpl).toHaveBeenCalledTimes(2)
  })

  it('preserves HTTP status and detail in API errors', async () => {
    const client = createApiClient({
      authMode: 'clerk',
      getToken: vi.fn().mockResolvedValue('token'),
      fetchImpl: vi.fn().mockResolvedValue(jsonResponse({ detail: 'Task not found' }, 404)),
    })

    await expect(client.getTask('missing')).rejects.toEqual(
      new ApiError(404, 'Task not found'),
    )
  })
})
