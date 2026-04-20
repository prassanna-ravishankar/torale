import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { connectorsEnabled } from '@/components/connectors/connectorsFlag';

interface SettingsTab {
  label: string;
  to: string;
}

export const SettingsTabs: React.FC = () => {
  const { pathname } = useLocation();
  const { user } = useAuth();
  const tabs: SettingsTab[] = [
    { label: 'Notifications', to: '/settings/notifications' },
    ...(connectorsEnabled(user)
      ? [{ label: 'Connectors', to: '/settings/connectors' }]
      : []),
  ];
  if (tabs.length < 2) return null;
  return (
    <nav className="mb-6 border-b-2 border-zinc-200 flex gap-1 overflow-x-auto">
      {tabs.map((tab) => {
        const active = pathname.startsWith(tab.to);
        return (
          <Link
            key={tab.to}
            to={tab.to}
            className={cn(
              'px-4 py-2 font-mono text-xs uppercase tracking-wider transition-colors border-b-2 -mb-[2px]',
              active
                ? 'border-zinc-900 text-zinc-900'
                : 'border-transparent text-zinc-500 hover:text-zinc-900'
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
};
