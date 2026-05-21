import React from 'react';
import { Mail, Webhook, Key, History } from 'lucide-react';
import { EmailManagementSection } from '@/components/settings/EmailManagementSection';
import { WebhookConfigSection } from '@/components/settings/WebhookConfigSection';
import { RecentDeliveriesSection } from '@/components/settings/RecentDeliveriesSection';
import { ApiKeyManagementSection } from '@/components/settings/ApiKeyManagementSection';
import { SettingsTabs } from '@/components/settings/SettingsTabs';
import styles from '@/components/settings/Settings.module.css';

/**
 * NotificationSettingsPage - settings panel for notification configuration.
 *
 * Layout: single editorial column (720px) inside the AppShell page wrapper.
 * AppShell already provides canvas background + outer page padding, so this
 * page only constrains the inner reading column.
 */
export const NotificationSettingsPage: React.FC = () => {
  return (
    <div className={styles.column}>
      <SettingsTabs />

      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <Mail className={styles.sectionHeadIcon} />
          <span className={styles.sectionLabel}>Notification emails</span>
          <span className={styles.sectionRule} />
        </div>
        <EmailManagementSection />
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <Webhook className={styles.sectionHeadIcon} />
          <span className={styles.sectionLabel}>Webhooks</span>
          <span className={styles.sectionRule} />
        </div>
        <WebhookConfigSection />
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <Key className={styles.sectionHeadIcon} />
          <span className={styles.sectionLabel}>API keys</span>
          <span className={styles.sectionRule} />
        </div>
        <ApiKeyManagementSection />
      </section>

      <section className={styles.section}>
        <div className={styles.sectionHead}>
          <History className={styles.sectionHeadIcon} />
          <span className={styles.sectionLabel}>Recent deliveries</span>
          <span className={styles.sectionRule} />
        </div>
        <RecentDeliveriesSection />
      </section>
    </div>
  );
};
