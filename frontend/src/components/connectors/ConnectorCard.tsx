import React, { useState } from 'react';
import { Loader2, Plug, Unplug, X } from 'lucide-react';
import { StatusBadge } from '@/components/torale';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
// ConnectionStatus drift is guarded by backend/tests/test_frontend_contract.py.
import type { AvailableToolkit, ConnectionStatus, UserConnection } from '@/types';
import { ConnectorLogo } from './ConnectorLogo';
import settingsStyles from '@/components/settings/Settings.module.css';
import styles from './Connectors.module.css';

interface ConnectorCardProps {
  toolkit: AvailableToolkit;
  connection: UserConnection | null;
  onConnect: (slug: string) => Promise<void>;
  onDisconnect: (slug: string) => Promise<void>;
  isWorking?: boolean;
}

function formatRelative(iso: string | null): string | null {
  if (!iso) return null;
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return null;
  // Clamp to zero so client/server clock drift can't render "-1m ago".
  const diffMs = Math.max(0, Date.now() - then);
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function statusBadge(status: ConnectionStatus | null): React.ReactNode {
  switch (status) {
    case 'ACTIVE':
      return <StatusBadge variant="active" label="Active" />;
    case 'INITIATED':
    case 'INITIALIZING':
      return <StatusBadge variant="running" label="Connecting" />;
    case 'EXPIRED':
      return <StatusBadge variant="failed" label="Expired" />;
    case 'FAILED':
      return <StatusBadge variant="failed" label="Failed" />;
    default:
      return null;
  }
}

export const ConnectorCard: React.FC<ConnectorCardProps> = ({
  toolkit,
  connection,
  onConnect,
  onDisconnect,
  isWorking = false,
}) => {
  const status = connection?.status ?? null;
  const [confirmOpen, setConfirmOpen] = useState(false);

  const isActive = status === 'ACTIVE';
  const isExpired = status === 'EXPIRED';
  const isFailed = status === 'FAILED';
  const isConnecting = status === 'INITIATED' || status === 'INITIALIZING';

  const handlePrimary = async () => {
    if (isWorking || isConnecting) return;
    await onConnect(toolkit.slug);
  };

  const lastUsed = isActive ? formatRelative(connection?.last_used_at ?? null) : null;
  const badge = statusBadge(status);

  return (
    <>
      <div className={styles.card}>
        <div className={styles.head}>
          <ConnectorLogo
            slug={toolkit.slug}
            displayName={toolkit.display_name}
            size="sm"
            muted={!isActive}
          />
          <div className={styles.headBody}>
            <h3 className={styles.name}>{toolkit.display_name}</h3>
            <p className={styles.slug}>{toolkit.slug}</p>
          </div>
        </div>

        <p className={styles.description}>{toolkit.description}</p>

        {(badge || lastUsed) && (
          <div className={styles.meta}>
            {badge}
            {lastUsed && (
              <span className={styles.metaTime}>Last used {lastUsed}</span>
            )}
          </div>
        )}

        {isExpired && (
          <p className={styles.reason}>Connection expired. Reconnect to resume.</p>
        )}
        {isFailed && connection?.status_reason && (
          <p className={styles.reason}>Last attempt: {connection.status_reason}</p>
        )}

        <div className={`${styles.foot} ${!isActive && !isConnecting ? styles.footFull : ''}`}>
          {isActive ? (
            <button
              type="button"
              className={settingsStyles.btnSecondary}
              onClick={() => setConfirmOpen(true)}
              disabled={isWorking}
            >
              <Unplug className="w-3.5 h-3.5" strokeWidth={1.5} />
              Disconnect
            </button>
          ) : isConnecting ? (
            <>
              <span className={styles.connectingNote}>
                <Loader2 className="w-3 h-3 animate-spin" strokeWidth={1.5} />
                Waiting for {toolkit.display_name}...
              </span>
              <button
                type="button"
                className={settingsStyles.btnGhost}
                onClick={() => onDisconnect(toolkit.slug)}
                disabled={isWorking}
              >
                <X className="w-3.5 h-3.5" strokeWidth={1.5} />
                Cancel
              </button>
            </>
          ) : isExpired || isFailed ? (
            <button
              type="button"
              className={settingsStyles.btnSecondary}
              onClick={handlePrimary}
              disabled={isWorking}
            >
              {isWorking ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
              ) : (
                <Plug className="w-3.5 h-3.5" strokeWidth={1.5} />
              )}
              Reconnect
            </button>
          ) : (
            <button
              type="button"
              className={settingsStyles.btnPrimary}
              onClick={handlePrimary}
              disabled={isWorking}
            >
              {isWorking ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
              ) : (
                <Plug className="w-3.5 h-3.5" strokeWidth={1.5} />
              )}
              Connect
            </button>
          )}
        </div>
      </div>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disconnect {toolkit.display_name}?</AlertDialogTitle>
            <AlertDialogDescription>
              The agent will stop using it on future runs. You can reconnect anytime.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className={settingsStyles.btnGhost}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className={settingsStyles.btnDanger}
              onClick={() => {
                setConfirmOpen(false);
                void onDisconnect(toolkit.slug);
              }}
            >
              Disconnect
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
