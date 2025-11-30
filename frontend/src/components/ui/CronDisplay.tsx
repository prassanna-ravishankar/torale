import React from 'react';
import cronstrue from 'cronstrue';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { cronUTCToLocal, getTimezoneAbbreviation } from '@/lib/timezoneUtils';

interface CronDisplayProps {
  cron: string;
  showRaw?: boolean; // Show raw cron in tooltip
  showTimezone?: boolean; // Show timezone abbreviation
  className?: string;
}

export const CronDisplay: React.FC<CronDisplayProps> = ({
  cron,
  showRaw = true,
  showTimezone = true,
  className = ''
}) => {
  try {
    // Convert UTC cron to local time for display
    const localCron = cronUTCToLocal(cron);

    const humanReadable = cronstrue.toString(localCron, {
      throwExceptionOnParseError: true,
      verbose: false,
      use24HourTimeFormat: false,
    });

    // Add timezone abbreviation if showing times
    const displayText = showTimezone && localCron !== cron
      ? `${humanReadable} ${getTimezoneAbbreviation()}`
      : humanReadable;

    if (showRaw) {
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <span className={className}>{displayText}</span>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-mono text-xs">{cron} (UTC)</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    return <span className={className}>{displayText}</span>;
  } catch (error) {
    // Fallback to raw cron if parsing fails
    return <span className={`font-mono ${className}`}>{cron}</span>;
  }
};
