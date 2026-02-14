import React from 'react';
import { SlackIntegration } from './integrations/SlackIntegration';

/**
 * IntegrationsSection - Container for all OAuth integrations
 * Currently only Slack, but extensible for Discord, Teams, etc.
 */
export const IntegrationsSection: React.FC = () => {
  return (
    <div className="space-y-6">
      <SlackIntegration />

      {/* Future integrations */}
      {/* <DiscordIntegration /> */}
      {/* <TeamsIntegration /> */}
    </div>
  );
};
