import React from 'react';
import cronstrue from 'cronstrue';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface CronDisplayProps {
  cron: string;
  showRaw?: boolean; // Show raw cron in tooltip
  className?: string;
}

export const CronDisplay: React.FC<CronDisplayProps> = ({
  cron,
  showRaw = true,
  className = ''
}) => {
  try {
    const humanReadable = cronstrue.toString(cron, {
      throwExceptionOnParseError: true,
      verbose: false,
      use24HourTimeFormat: false,
    });

    if (showRaw) {
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <span className={className}>{humanReadable}</span>
            </TooltipTrigger>
            <TooltipContent>
              <p className="font-mono text-xs">{cron}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    return <span className={className}>{humanReadable}</span>;
  } catch (error) {
    // Fallback to raw cron if parsing fails
    return <span className={`font-mono ${className}`}>{cron}</span>;
  }
};
