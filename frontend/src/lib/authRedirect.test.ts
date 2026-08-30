import { describe, expect, it } from 'vitest'

import { getSignInRedirect } from './authRedirect'

describe('getSignInRedirect', () => {
  it('preserves a complete deep link as the return URL', () => {
    expect(getSignInRedirect(
      '/dashboard/tasks/watch/id',
      'tab=history&filter=sent',
    )).toBe(
      '/sign-in?redirect_url=%2Fdashboard%2Ftasks%2Fwatch%2Fid%3Ftab%3Dhistory%26filter%3Dsent',
    )
  })

  it('does not add a question mark when there is no query', () => {
    expect(getSignInRedirect('/dashboard', '')).toBe('/sign-in?redirect_url=%2Fdashboard')
  })
})
