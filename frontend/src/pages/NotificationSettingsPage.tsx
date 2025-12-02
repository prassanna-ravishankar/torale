import React from 'react';
import { Link } from 'react-router-dom';
import { Settings, Mail, Webhook, Key, History } from 'lucide-react';
import { EmailManagementSection } from '@/components/settings/EmailManagementSection';
import { WebhookConfigSection } from '@/components/settings/WebhookConfigSection';
import { NotificationHistorySection } from '@/components/settings/NotificationHistorySection';
import { ApiKeyManagementSection } from '@/components/settings/ApiKeyManagementSection';

/**
 * NotificationSettingsPage - Brutalist settings panel
 * Mission Control for notification configuration
 */
export const NotificationSettingsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-zinc-50">
      <main className="p-4 md:p-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono mb-2">
            <Link to="/dashboard" className="hover:text-zinc-900 transition-colors">Dashboard</Link>
            <span>/</span>
            <span className="text-zinc-900">Settings</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-zinc-900 text-white w-10 h-10 flex items-center justify-center">
              <Settings className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold font-grotesk tracking-tight">Settings</h1>
              <p className="text-sm text-zinc-500 font-mono">Configure notifications and API access</p>
            </div>
          </div>
        </header>

        {/* Settings Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left Column */}
          <div className="space-y-6">
            {/* Email Management */}
            <section>
              <div className="flex items-center gap-2 mb-3">
                <Mail className="h-4 w-4 text-zinc-400" />
                <h2 className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">Email Addresses</h2>
              </div>
              <EmailManagementSection />
            </section>

            {/* Webhook Configuration */}
            <section>
              <div className="flex items-center gap-2 mb-3">
                <Webhook className="h-4 w-4 text-zinc-400" />
                <h2 className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">Webhooks</h2>
              </div>
              <WebhookConfigSection />
            </section>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            {/* API Key Management */}
            <section>
              <div className="flex items-center gap-2 mb-3">
                <Key className="h-4 w-4 text-zinc-400" />
                <h2 className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">API Keys</h2>
              </div>
              <ApiKeyManagementSection />
            </section>

            {/* Notification History */}
            <section>
              <div className="flex items-center gap-2 mb-3">
                <History className="h-4 w-4 text-zinc-400" />
                <h2 className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">Notification History</h2>
              </div>
              <NotificationHistorySection />
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};
