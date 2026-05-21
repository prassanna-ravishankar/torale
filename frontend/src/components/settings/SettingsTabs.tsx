'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/AuthContext';
import { connectorsEnabled } from '@/components/connectors/connectorsFlag';
import styles from './Settings.module.css';

interface SettingsTab {
  label: string;
  to: string;
}

export const SettingsTabs: React.FC = () => {
  const pathname = usePathname() || '';
  const { user } = useAuth();
  const tabs: SettingsTab[] = [
    { label: 'Notifications', to: '/settings/notifications' },
    ...(connectorsEnabled(user)
      ? [{ label: 'Connectors', to: '/settings/connectors' }]
      : []),
  ];
  if (tabs.length < 2) return null;
  return (
    <nav className={styles.tabs}>
      {tabs.map((tab) => {
        const active = pathname.startsWith(tab.to);
        return (
          <Link
            key={tab.to}
            href={tab.to}
            className={cn(styles.tab, active && styles.tabActive)}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
};
