import React, { useEffect, useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import api from '@/lib/api';
import type { AvailableToolkit, UserConnection } from '@/types';
import { useAuth } from '@/contexts/AuthContext';
import { ReconnectButton } from './ReconnectButton';
import { connectorsEnabled } from './connectorsFlag';

interface ConnectorDegradationBannerProps {
  attachedSlugs: string[];
}

interface DegradedEntry {
  slug: string;
  displayName: string;
  reason: 'disconnected' | 'expired' | 'failed';
}

// Shows one strip per attached-but-unhealthy connector on a task.
// Renders null when every attached slug is ACTIVE (or when none are
// attached -- the common case until the picker lands).
export const ConnectorDegradationBanner: React.FC<ConnectorDegradationBannerProps> = ({
  attachedSlugs,
}) => {
  const { user } = useAuth();
  const enabled = connectorsEnabled(user);
  const [degraded, setDegraded] = useState<DegradedEntry[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!enabled || attachedSlugs.length === 0) {
      setLoaded(true);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const [available, connections] = await Promise.all([
          api.getAvailableToolkits(),
          api.getUserConnections(),
        ]);
        if (cancelled) return;
        const nameBySlug = new Map<string, string>(
          available.map((t: AvailableToolkit) => [t.slug, t.display_name])
        );
        const connBySlug = new Map<string, UserConnection>(
          connections.map((c: UserConnection) => [c.toolkit_slug, c])
        );
        const entries: DegradedEntry[] = [];
        for (const slug of attachedSlugs) {
          const conn = connBySlug.get(slug);
          const displayName = nameBySlug.get(slug) ?? slug;
          if (!conn || conn.status === 'INACTIVE' || conn.status === null) {
            entries.push({ slug, displayName, reason: 'disconnected' });
          } else if (conn.status === 'EXPIRED') {
            entries.push({ slug, displayName, reason: 'expired' });
          } else if (conn.status === 'FAILED') {
            entries.push({ slug, displayName, reason: 'failed' });
          }
        }
        setDegraded(entries);
      } catch {
        // Soft-fail: banner is a nice-to-have, never blocks task view.
      } finally {
        if (!cancelled) setLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [attachedSlugs, enabled]);

  if (!loaded || degraded.length === 0) return null;

  return (
    <div className="mb-4 space-y-2">
      {degraded.map((entry) => (
        <div
          key={entry.slug}
          className="flex items-start gap-3 border-2 border-red-200 bg-red-50 p-3"
        >
          <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-zinc-900">
              <span className="font-grotesk font-semibold">{entry.displayName}</span>{' '}
              {entry.reason === 'expired' && 'connection expired.'}
              {entry.reason === 'disconnected' && 'is no longer connected.'}
              {entry.reason === 'failed' && 'connection is failing.'}
            </p>
            <p className="font-mono text-[11px] text-zinc-500 mt-0.5">
              This task will skip {entry.displayName} until reconnected.
            </p>
          </div>
          <ReconnectButton
            toolkitSlug={entry.slug}
            displayName={entry.displayName}
            size="sm"
            className="bg-red-600 hover:bg-red-700 text-white"
          />
        </div>
      ))}
    </div>
  );
};
