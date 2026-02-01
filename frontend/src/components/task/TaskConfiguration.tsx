import React from 'react';
import { Search, Bell, Mail, Webhook, CheckCircle } from 'lucide-react';
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { InfoCard, CollapsibleSection, BrutalistSwitch } from "@/components/torale";
import { NotificationChannelBadges } from "@/components/notifications/NotificationChannelBadges";
import type { Task } from '@/types';

interface TaskConfigurationProps {
  task: Task;
  configExpanded: boolean;
  onConfigExpandedChange: (expanded: boolean) => void;
  onToggle: () => void;
}

const NOTIFY_BEHAVIOR_LABELS = {
  'once': 'Once only',
  'always': 'Every time',
  'track_state': 'On changes'
} as const;

// Shared status rendering logic
const renderTaskStatus = (task: Task, onToggle: () => void) => {
  if (task.state === 'completed') {
    return {
      badge: (
        <Badge variant="default" className="bg-emerald-100 text-emerald-900 border border-emerald-900 text-xs">
          <CheckCircle className="h-3 w-3 mr-1" />
          Completed
        </Badge>
      ),
      button: (
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className="text-xs h-7 px-2 font-mono uppercase tracking-wider hover:bg-zinc-100"
        >
          Re-activate
        </Button>
      )
    };
  }

  return {
    badge: null,
    button: (
      <div className="flex items-center gap-1.5">
        <BrutalistSwitch
          checked={task.state === 'active'}
          onCheckedChange={onToggle}
        />
        <span className={`text-xs font-mono ${task.state === 'active' ? 'text-zinc-700' : 'text-zinc-900 font-bold'}`}>
          {task.state === 'active' ? "Active" : "Paused"}
        </span>
      </div>
    )
  };
};

export const TaskConfiguration: React.FC<TaskConfigurationProps> = ({
  task,
  configExpanded,
  onConfigExpandedChange,
  onToggle,
}) => {
  const statusControls = renderTaskStatus(task, onToggle);
  // Compact list for mobile/tablet
  const configList = (
    <div className="space-y-3 p-4 bg-white border-t-2 border-zinc-200">
      {/* Trigger Condition */}
      <div className="flex items-start gap-3">
        <Search className="h-4 w-4 text-zinc-500 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-xs font-mono text-zinc-500 uppercase tracking-wider mb-1">Trigger</div>
          <p className="text-sm text-zinc-900 leading-relaxed">{task.condition_description}</p>
        </div>
      </div>

      {/* When to Notify + Status */}
      <div className="flex items-start gap-3">
        <Bell className="h-4 w-4 text-zinc-500 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-xs font-mono text-zinc-500 uppercase tracking-wider mb-1">Notify</div>
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-mono text-zinc-900">
                {NOTIFY_BEHAVIOR_LABELS[task.notify_behavior]}
              </span>
              <span className="text-zinc-400">•</span>
              {statusControls.badge || statusControls.button}
            </div>
            {statusControls.badge && statusControls.button}
          </div>
        </div>
      </div>

      {/* Notification Channels */}
      <div className="flex items-start gap-3">
        <Mail className="h-4 w-4 text-zinc-500 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="text-xs font-mono text-zinc-500 uppercase tracking-wider mb-1">Channels</div>
          {task.notification_channels && task.notification_channels.length > 0 ? (
            <div className="text-sm text-zinc-900 space-y-1">
              {task.notification_channels.includes('email') && (
                <div className="truncate">
                  email ({task.notification_email || 'Default (Clerk email)'})
                </div>
              )}
              {task.notification_channels.includes('webhook') && (
                <div className="truncate">
                  webhook ({task.webhook_url || 'Default webhook'})
                </div>
              )}
            </div>
          ) : (
            <span className="text-sm text-zinc-500">None configured</span>
          )}
        </div>
      </div>
    </div>
  );

  // Card grid for desktop
  const configCards = (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <InfoCard icon={Search} label="Trigger Condition">
        <p className="text-sm text-zinc-700 leading-relaxed">{task.condition_description}</p>
      </InfoCard>

      <InfoCard icon={Bell} label="When to Notify">
        <p className="text-sm font-mono uppercase tracking-wider text-zinc-700">
          {NOTIFY_BEHAVIOR_LABELS[task.notify_behavior]}
        </p>
        <div className="flex items-center gap-2 mt-3">
          {statusControls.badge ? (
            <div className="flex flex-col gap-2">
              {statusControls.badge}
              {statusControls.button}
            </div>
          ) : (
            statusControls.button
          )}
        </div>
      </InfoCard>

      <InfoCard icon={Mail} label="Notification Channels">
        {task.notification_channels && task.notification_channels.length > 0 ? (
          <div className="space-y-3">
            <NotificationChannelBadges
              channels={task.notification_channels}
              notificationEmail={task.notification_email}
              webhookUrl={task.webhook_url}
            />
            <div className="space-y-1 text-xs font-mono text-zinc-600">
              {task.notification_channels.includes('email') && (
                <div className="flex items-start gap-1.5">
                  <Mail className="h-3 w-3 mt-0.5 shrink-0" />
                  <span className="truncate">
                    {task.notification_email || 'Default (Clerk email)'}
                  </span>
                </div>
              )}
              {task.notification_channels.includes('webhook') && (
                <div className="flex items-start gap-1.5">
                  <Webhook className="h-3 w-3 mt-0.5 shrink-0" />
                  <span className="truncate">
                    {task.webhook_url || 'Default webhook'}
                  </span>
                </div>
              )}
            </div>
          </div>
        ) : (
          <p className="text-sm font-mono text-zinc-600">No channels configured</p>
        )}
      </InfoCard>
    </div>
  );

  return (
    <>
      {/* Mobile: Collapsible with list */}
      <div className="lg:hidden">
        <CollapsibleSection
          title="Task Configuration"
          open={configExpanded}
          onOpenChange={onConfigExpandedChange}
          variant="mobile"
        >
          {configList}
        </CollapsibleSection>
      </div>

      {/* Desktop: Always visible cards */}
      <div className="hidden lg:block">
        {configCards}
      </div>
    </>
  );
};
