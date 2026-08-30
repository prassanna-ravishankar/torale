import { describe, expect, it } from 'vitest'

import { ownerWatchPath, publicWatchPath, watchRssPath } from './watchRoutes'

describe('watch route helpers', () => {
  it('builds owner, public, and RSS paths from one encoded identifier', () => {
    expect(ownerWatchPath('watch/id')).toBe('/dashboard/tasks/watch%2Fid')
    expect(publicWatchPath('watch/id')).toBe('/tasks/watch%2Fid')
    expect(watchRssPath('watch/id')).toBe('/tasks/watch%2Fid/rss')
  })
})
