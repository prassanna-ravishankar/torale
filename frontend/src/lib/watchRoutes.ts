const idSegment = (taskId: string): string => encodeURIComponent(taskId)

export const ownerWatchPath = (taskId: string): string =>
  `/dashboard/tasks/${idSegment(taskId)}`

export const publicWatchPath = (taskId: string): string =>
  `/tasks/${idSegment(taskId)}`

export const watchRssPath = (taskId: string): string =>
  `${publicWatchPath(taskId)}/rss`
