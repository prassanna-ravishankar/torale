import type { FeedExecution } from '@/types'

const baseUrl = () => process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const readJson = async <T>(response: Response): Promise<T> => {
  if (!response.ok) throw new Error(`Public API request failed: ${response.status}`)
  return response.json()
}

export const publicApi = {
  async getPublicFeed(limit = 50): Promise<FeedExecution[]> {
    const params = new URLSearchParams({ limit: String(limit) })
    return readJson(await fetch(`${baseUrl()}/api/v1/public/feed?${params}`))
  },
}
