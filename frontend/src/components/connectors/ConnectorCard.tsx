import React, { useState } from 'react';
import { Loader2, RefreshCw, Unplug, X } from 'lucide-react';
import { BrutalistCard, StatusBadge, ActionMenu, type Action } from '@/components/torale';
import { Button } from '@/components/ui/button';
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
// Mirror of backend ConnectionStatus StrEnum (backend/src/torale/connectors/client.py); keep in sync.
import type { AvailableToolkit, ConnectionStatus, UserConnection } from '@/types';
import { cn } from '@/lib/utils';
import { ConnectorLogo } from './ConnectorLogo';

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
  const diffMs = Date.now() - then;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function statusVariant(status: ConnectionStatus | null): {
  variant: 'active' | 'running' | 'failed' | 'pending' | null;
  label?: string;
} {
  switch (status) {
    case 'ACTIVE':
      return { variant: 'active', label: 'Active' };
    case 'INITIATED':
    case 'INITIALIZING':
      return { variant: 'running', label: 'Connecting' };
    case 'EXPIRED':
      return { variant: 'failed', label: 'Expired' };
    case 'FAILED':
      return { variant: 'failed', label: 'Failed' };
    case 'INACTIVE':
    case null:
    case undefined:
      return { variant: null };
    default:
      return { variant: null };
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
  const badge = statusVariant(status);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const isActive = status === 'ACTIVE';
  const isExpired = status === 'EXPIRED';
  const isFailed = status === 'FAILED';
  const isConnecting = status === 'INITIATED' || status === 'INITIALIZING';

  const accentClass = cn(
    isExpired && 'border-l-4 border-l-red-500 bg-red-50/40',
    isFailed && 'border-l-4 border-l-amber-500 bg-amber-50/40',
    isConnecting && 'border-l-4 border-l-amber-500'
  );

  const handlePrimary = async () => {
    if (isWorking || isConnecting) return;
    await onConnect(toolkit.slug);
  };

  const manageActions: Action[] = [
    {
      id: 'reconnect',
      label: 'Reconnect',
      icon: RefreshCw,
      onClick: () => {
        void onConnect(toolkit.slug);
      },
    },
    {
      id: 'disconnect',
      label: 'Disconnect',
      icon: Unplug,
      variant: 'destructive',
      separator: true,
      onClick: () => setConfirmOpen(true),
    },
  ];

  return (
    <>
      <BrutalistCard className={cn('p-0', accentClass)} animate hoverEffect={!isConnecting}>
        <div className="flex items-start gap-3 p-5 pb-4">
          <ConnectorLogo
            slug={toolkit.slug}
            displayName={toolkit.display_name}
            muted={!isActive}
            className={cn(isConnecting && 'animate-pulse')}
          />
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <h3 className="font-grotesk text-base font-bold tracking-tight text-zinc-900">
                  {toolkit.display_name}
                </h3>
                <p className="font-mono text-[11px] text-zinc-500 truncate">
                  {toolkit.slug}
                </p>
              </div>
              {badge.variant && (
                <StatusBadge variant={badge.variant} label={badge.label} />
              )}
            </div>
          </div>
        </div>

        <div className="border-t border-zinc-200 px-5 py-4 space-y-2">
          <p className="text-sm text-zinc-700 leading-snug">{toolkit.description}</p>
          {isActive && (
            <dl className="space-y-1 pt-1 font-mono text-[11px] text-zinc-500">
              <div className="flex gap-2">
                <dt>Last used:</dt>
                <dd className="text-zinc-700">
                  {formatRelative(connection?.last_used_at ?? null) ?? 'Never used'}
                </dd>
              </div>
              {connection?.connected_at && (
                <div className="flex gap-2">
                  <dt>Connected:</dt>
                  <dd className="text-zinc-700">
                    {formatRelative(connection.connected_at) ?? ''}
                  </dd>
                </div>
              )}
            </dl>
          )}
          {isExpired && (
            <p className="font-mono text-[11px] text-red-600">
              Connection expired. Reconnect to resume.
            </p>
          )}
          {isFailed && connection?.status_reason && (
            <p className="font-mono text-[11px] text-amber-700">
              Last attempt: {connection.status_reason}
            </p>
          )}
        </div>

        <div className="border-t border-zinc-200 px-5 py-3 flex items-center justify-between gap-2">
          {isActive ? (
            <ActionMenu
              actions={manageActions}
              triggerClassName="ml-auto text-zinc-500 hover:text-zinc-900 transition-colors"
            />
          ) : isConnecting ? (
            <>
              <span className="inline-flex items-center gap-2 font-mono text-xs text-zinc-500">
                <Loader2 className="w-3 h-3 animate-spin" />
                Waiting for {toolkit.display_name}...
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDisconnect(toolkit.slug)}
                disabled={isWorking}
              >
                <X className="w-3 h-3 mr-1" /> Cancel
              </Button>
            </>
          ) : isExpired ? (
            <Button
              onClick={handlePrimary}
              disabled={isWorking}
              className="w-full bg-zinc-900 hover:bg-zinc-800"
            >
              {isWorking ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Reconnect'}
            </Button>
          ) : isFailed ? (
            <Button
              onClick={handlePrimary}
              disabled={isWorking}
              variant="outline"
              className="w-full"
            >
              {isWorking ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Retry connection'}
            </Button>
          ) : (
            <Button
              onClick={handlePrimary}
              disabled={isWorking}
              className="w-full bg-zinc-900 hover:bg-zinc-800"
            >
              {isWorking ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Connect'}
            </Button>
          )}
        </div>
      </BrutalistCard>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disconnect {toolkit.display_name}?</AlertDialogTitle>
            <AlertDialogDescription>
              The agent will stop using it on future runs. You can reconnect anytime.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                setConfirmOpen(false);
                void onDisconnect(toolkit.slug);
              }}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              Disconnect
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
