/**
 * Timezone conversion utilities for cron schedules
 *
 * Philosophy: Backend stores everything in UTC, frontend displays in user's browser timezone
 * Trade-off: Schedules shift by 1 hour during DST transitions (normal behavior)
 */

/**
 * Get the user's current timezone offset split into hours and minutes
 * @returns Object with hours and minutes offset
 * Example: Mumbai (UTC+5:30) returns { hours: -5, minutes: -30 }
 *          PST (UTC-8) returns { hours: 8, minutes: 0 }
 */
export function getTimezoneOffsetParts(): { hours: number; minutes: number } {
  const totalMinutes = new Date().getTimezoneOffset();
  // getTimezoneOffset returns positive for UTC- and negative for UTC+
  const hours = Math.trunc(totalMinutes / 60); // Use trunc to preserve sign
  const minutes = totalMinutes % 60; // Remainder keeps same sign as totalMinutes
  return { hours, minutes };
}

/**
 * Get the user's current timezone offset in hours
 * @deprecated Use getTimezoneOffsetParts() for accurate conversion with minute offsets
 * @returns Offset in hours (negative for UTC+, positive for UTC-)
 * Example: PST (UTC-8) returns 8, JST (UTC+9) returns -9
 */
export function getTimezoneOffsetHours(): number {
  const offsetMinutes = new Date().getTimezoneOffset();
  // getTimezoneOffset returns positive for UTC- and negative for UTC+
  // We flip the sign so UTC-8 (PST) = +8, UTC+9 (JST) = -9
  return offsetMinutes / 60;
}

/**
 * Convert local hour to UTC hour
 * @param localHour Hour in user's local timezone (0-23)
 * @returns Hour in UTC (0-23), wrapped if necessary
 */
export function localHourToUTC(localHour: number): number {
  const offsetHours = getTimezoneOffsetHours();
  let utcHour = localHour + offsetHours;

  // Handle wrapping (e.g., 23 + 2 = 1, 0 - 5 = 19)
  if (utcHour >= 24) {
    utcHour -= 24;
  } else if (utcHour < 0) {
    utcHour += 24;
  }

  return Math.floor(utcHour);
}

/**
 * Convert UTC hour to local hour
 * @deprecated Use utcTimeToLocal() for accurate conversion with minute offsets
 * @param utcHour Hour in UTC (0-23)
 * @returns Hour in user's local timezone (0-23), wrapped if necessary
 */
export function utcHourToLocal(utcHour: number): number {
  const offsetHours = getTimezoneOffsetHours();
  let localHour = utcHour - offsetHours;

  // Handle wrapping
  if (localHour >= 24) {
    localHour -= 24;
  } else if (localHour < 0) {
    localHour += 24;
  }

  return Math.floor(localHour);
}

/**
 * Convert local time (hour + minute) to UTC time
 * Handles timezones with minute offsets (e.g., India UTC+5:30)
 * @param localHour Hour in user's local timezone (0-23)
 * @param localMinute Minute in user's local timezone (0-59)
 * @returns Object with UTC hour and minute
 */
export function localTimeToUTC(localHour: number, localMinute: number): { hour: number; minute: number } {
  const offset = getTimezoneOffsetParts();

  // Add offset to convert to UTC (offset is already in correct sign)
  let utcHour = localHour + offset.hours;
  let utcMinute = localMinute + offset.minutes;

  // Handle minute overflow/underflow
  if (utcMinute >= 60) {
    utcMinute -= 60;
    utcHour += 1;
  } else if (utcMinute < 0) {
    utcMinute += 60;
    utcHour -= 1;
  }

  // Handle hour wrapping
  if (utcHour >= 24) {
    utcHour -= 24;
  } else if (utcHour < 0) {
    utcHour += 24;
  }

  return { hour: utcHour, minute: utcMinute };
}

/**
 * Convert UTC time (hour + minute) to local time
 * Handles timezones with minute offsets (e.g., India UTC+5:30)
 * @param utcHour Hour in UTC (0-23)
 * @param utcMinute Minute in UTC (0-59)
 * @returns Object with local hour and minute
 */
export function utcTimeToLocal(utcHour: number, utcMinute: number): { hour: number; minute: number } {
  const offset = getTimezoneOffsetParts();

  // Subtract offset to convert to local (offset is already in correct sign)
  let localHour = utcHour - offset.hours;
  let localMinute = utcMinute - offset.minutes;

  // Handle minute overflow/underflow
  if (localMinute >= 60) {
    localMinute -= 60;
    localHour += 1;
  } else if (localMinute < 0) {
    localMinute += 60;
    localHour -= 1;
  }

  // Handle hour wrapping
  if (localHour >= 24) {
    localHour -= 24;
  } else if (localHour < 0) {
    localHour += 24;
  }

  return { hour: localHour, minute: localMinute };
}

/**
 * Get abbreviated timezone name (PST, EST, JST, etc.)
 * Falls back to UTC offset if abbreviation not available
 */
export function getTimezoneAbbreviation(): string {
  try {
    // Try to get timezone abbreviation from Intl.DateTimeFormat
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZoneName: 'short',
    });

    const parts = formatter.formatToParts(new Date());
    const timeZonePart = parts.find(part => part.type === 'timeZoneName');

    if (timeZonePart && timeZonePart.value) {
      return timeZonePart.value;
    }
  } catch (error) {
    // Fallback if Intl fails
  }

  // Fallback to UTC offset format
  const offsetHours = -getTimezoneOffsetHours(); // Flip sign for display (UTC-8, not +8)
  const sign = offsetHours >= 0 ? '+' : '-';
  const absOffset = Math.abs(offsetHours);
  return `UTC${sign}${absOffset}`;
}

/**
 * Get full timezone name (IANA format like "America/Los_Angeles")
 */
export function getTimezoneIANA(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (error) {
    return 'UTC';
  }
}

/**
 * Convert a cron expression from UTC to local time (for display)
 * Handles timezones with minute offsets (e.g., India UTC+5:30)
 * Only handles simple daily/weekly/monthly patterns with specific hours
 * @param cronUTC Cron expression in UTC (e.g., "30 17 * * *")
 * @returns Cron expression in local time (e.g., "0 23 * * *" for India), or original if can't parse
 */
export function cronUTCToLocal(cronUTC: string): string {
  const parts = cronUTC.split(' ');
  if (parts.length !== 5) return cronUTC;

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;

  // Only convert if hour is a specific number (not *, */N, or ranges)
  if (hour === '*' || hour.includes('/') || hour.includes(',') || hour.includes('-')) {
    return cronUTC;
  }

  // Only convert if minute is a specific number
  if (minute === '*' || minute.includes('/') || minute.includes(',') || minute.includes('-')) {
    return cronUTC;
  }

  const utcHour = parseInt(hour, 10);
  const utcMinute = parseInt(minute, 10);

  if (isNaN(utcHour) || utcHour < 0 || utcHour > 23) {
    return cronUTC;
  }
  if (isNaN(utcMinute) || utcMinute < 0 || utcMinute > 59) {
    return cronUTC;
  }

  const localTime = utcTimeToLocal(utcHour, utcMinute);

  return `${localTime.minute} ${localTime.hour} ${dayOfMonth} ${month} ${dayOfWeek}`;
}

/**
 * Convert a cron expression from local time to UTC (for storage)
 * Handles timezones with minute offsets (e.g., India UTC+5:30)
 * Only handles simple daily/weekly/monthly patterns with specific hours
 * @param cronLocal Cron expression in local time (e.g., "0 9 * * *")
 * @returns Cron expression in UTC (e.g., "30 3 * * *" for India)
 */
export function cronLocalToUTC(cronLocal: string): string {
  const parts = cronLocal.split(' ');
  if (parts.length !== 5) return cronLocal;

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;

  // Only convert if hour is a specific number
  if (hour === '*' || hour.includes('/') || hour.includes(',') || hour.includes('-')) {
    return cronLocal;
  }

  // Only convert if minute is a specific number
  if (minute === '*' || minute.includes('/') || minute.includes(',') || minute.includes('-')) {
    return cronLocal;
  }

  const localHour = parseInt(hour, 10);
  const localMinute = parseInt(minute, 10);

  if (isNaN(localHour) || localHour < 0 || localHour > 23) {
    return cronLocal;
  }
  if (isNaN(localMinute) || localMinute < 0 || localMinute > 59) {
    return cronLocal;
  }

  const utcTime = localTimeToUTC(localHour, localMinute);

  return `${utcTime.minute} ${utcTime.hour} ${dayOfMonth} ${month} ${dayOfWeek}`;
}
