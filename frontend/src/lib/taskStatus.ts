/**
 * Task status logic - derive task activity state from current data.
 *
 * This is the single source of truth for task status across the frontend.
 * All status display logic should use these functions.
 */

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
 * Derive task status from is_active and latest execution result.
 *
 * Logic:
 * - Active (is_active=true): Task is monitoring on schedule
 * - Completed (is_active=false + last_execution.condition_met=true):
 *     Auto-stopped after notify_behavior="once" success
 * - Paused (is_active=false + last_execution.condition_met=false/null):
 *     User manually stopped
 *
 * @param isActive - Whether task is currently active (monitoring)
 * @param lastExecutionConditionMet - Whether the latest execution met its condition
 *                                     (null/undefined if task never executed)
 * @returns TaskStatusInfo with activity state and display metadata
 */
export function getTaskStatus(
  isActive: boolean,
  lastExecutionConditionMet: boolean | null | undefined
): TaskStatusInfo {
  if (isActive) {
    return {
      activityState: TaskActivityState.ACTIVE,
      iconName: 'Activity',
      label: 'Monitoring',
      color: 'green',
      description: 'Actively checking on schedule',
    };
  }

  // Inactive - determine why
  if (lastExecutionConditionMet) {
    return {
      activityState: TaskActivityState.COMPLETED,
      iconName: 'CheckCircle',
      label: 'Completed',
      color: 'blue',
      description: 'Notified once and auto-stopped',
    };
  }

  return {
    activityState: TaskActivityState.PAUSED,
    iconName: 'Pause',
    label: 'Paused',
    color: 'yellow',
    description: 'Manually paused by user',
  };
}
