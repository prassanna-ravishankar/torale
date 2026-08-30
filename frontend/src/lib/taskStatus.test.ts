import { describe, expect, it } from 'vitest'

import { getTaskStatus, TaskActivityState } from './taskStatus'

describe('getTaskStatus', () => {
  it.each([
    ['active', TaskActivityState.ACTIVE, 'Activity', 'Watching', 'green'],
    ['completed', TaskActivityState.COMPLETED, 'CheckCircle', 'Completed', 'blue'],
    ['paused', TaskActivityState.PAUSED, 'Pause', 'Paused', 'yellow'],
  ] as const)('maps %s tasks to their display state', (state, activityState, iconName, label, color) => {
    expect(getTaskStatus(state)).toMatchObject({ activityState, iconName, label, color })
  })

  it('keeps the activity-state values distinct', () => {
    expect(new Set(Object.values(TaskActivityState)).size).toBe(3)
  })
})
