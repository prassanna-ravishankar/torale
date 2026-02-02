/**
 * Task status logic - now uses explicit state from backend.
 *
 * This is the single source of truth for task status across the frontend.
 * All status display logic should use these functions.
 */

import type { TaskState } from '@/types';

export enum TaskActivityState {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  PAUSED = 'paused',
}

export interface TaskStatusInfo {
  activityState: TaskActivityState;
  iconName: 'Activity' | 'CheckCircle' | 'Pause';  // Lucide icon names
  label: string;
  color: string;
  description: string;
}

/**
 * Get task status directly from state (no more derivation logic).
 *
 * The backend now provides explicit state, so we just map it to display metadata.
 *
 * @param state - Task state from backend ('active' | 'paused' | 'completed')
 * @returns TaskStatusInfo with activity state and display metadata
 */
export function getTaskStatus(state: TaskState): TaskStatusInfo {
  const configs: Record<TaskState, TaskStatusInfo> = {
    active: {
      activityState: TaskActivityState.ACTIVE,
      iconName: 'Activity',
      label: 'Monitoring',
      color: 'green',
      description: 'Actively monitoring',
    },
    completed: {
      activityState: TaskActivityState.COMPLETED,
      iconName: 'CheckCircle',
      label: 'Completed',
      color: 'blue',
      description: 'Monitoring complete',
    },
    paused: {
      activityState: TaskActivityState.PAUSED,
      iconName: 'Pause',
      label: 'Paused',
      color: 'yellow',
      description: 'Manually paused by user',
    },
  };

  return configs[state];
}
