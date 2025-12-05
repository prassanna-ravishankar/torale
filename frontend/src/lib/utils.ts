import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Calculate duration in seconds between two timestamps
 * @param startTime - ISO 8601 timestamp string
 * @param endTime - ISO 8601 timestamp string
 * @returns Duration in seconds, rounded to nearest integer
 */
export function calculateDurationInSeconds(startTime: string, endTime: string): number {
  return Math.round((new Date(endTime).getTime() - new Date(startTime).getTime()) / 1000)
}

/**
 * Format duration for display
 * @param startTime - ISO 8601 timestamp string (optional)
 * @param endTime - ISO 8601 timestamp string (optional)
 * @param runningLabel - Label to show if task is still running (default: 'In progress')
 * @returns Formatted duration string (e.g., "42s") or fallback label
 */
export function formatDuration(
  startTime: string | null | undefined,
  endTime: string | null | undefined,
  runningLabel: string = 'In progress'
): string {
  if (startTime && endTime) {
    return `${calculateDurationInSeconds(startTime, endTime)}s`
  }
  return runningLabel
}

/**
 * Format timestamp as relative time (e.g., "2h ago", "Just now")
 * @param dateString - ISO 8601 timestamp string
 * @returns Formatted relative time string
 */
export function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    return 'Invalid date';
  }

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  const MINS_IN_HOUR = 60;
  const MINS_IN_DAY = MINS_IN_HOUR * 24;
  const MINS_IN_WEEK = MINS_IN_DAY * 7;

  if (diffMins < 1) return 'Just now';
  if (diffMins < MINS_IN_HOUR) return `${diffMins}m ago`;
  if (diffMins < MINS_IN_DAY) return `${Math.floor(diffMins / MINS_IN_HOUR)}h ago`;
  if (diffMins < MINS_IN_WEEK) return `${Math.floor(diffMins / MINS_IN_DAY)}d ago`;
  return date.toLocaleDateString();
}
