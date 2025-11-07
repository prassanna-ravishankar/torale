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
