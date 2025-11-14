import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Mail, Webhook } from 'lucide-react';
import type { NotificationChannelType } from '@/types';

interface NotificationChannelBadgesProps {
  channels: NotificationChannelType[];
  notificationEmail?: string | null;
  webhookUrl?: string | null;
  className?: string;
}

export const NotificationChannelBadges: React.FC<NotificationChannelBadgesProps> = ({
  channels,
  notificationEmail,
  webhookUrl,
  className = '',
}) => {
  if (!channels || channels.length === 0) {
    return null;
  }

  const hasEmail = channels.includes('email');
  const hasWebhook = channels.includes('webhook');

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <TooltipProvider>
        {hasEmail && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant="secondary" className="gap-1">
                <Mail className="h-3 w-3" />
                Email
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p className="text-xs">
                {notificationEmail ? `Custom: ${notificationEmail}` : 'Default (Clerk email)'}
              </p>
            </TooltipContent>
          </Tooltip>
        )}

        {hasWebhook && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Badge variant="secondary" className="gap-1">
                <Webhook className="h-3 w-3" />
                Webhook
              </Badge>
            </TooltipTrigger>
            <TooltipContent>
              <p className="text-xs max-w-xs truncate">
                {webhookUrl ? webhookUrl : 'Default webhook'}
              </p>
            </TooltipContent>
          </Tooltip>
        )}
      </TooltipProvider>
    </div>
  );
};
