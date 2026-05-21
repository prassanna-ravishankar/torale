import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Loader2, Plug } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';
import type { AvailableToolkit, UserConnection } from '@/types';
import { EmptyState } from '@/components/torale';
import { SettingsTabs } from '@/components/settings/SettingsTabs';
import { ConnectorCard } from '@/components/connectors/ConnectorCard';
import styles from '@/components/connectors/Connectors.module.css';

const POLL_INTERVAL_MS = 10_000;
const POLL_WINDOW_MS = 10 * 60_000;

export const ConnectorsPage: React.FC = () => {
  const [toolkits, setToolkits] = useState<AvailableToolkit[]>([]);
  const [connections, setConnections] = useState<UserConnection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [workingSlugs, setWorkingSlugs] = useState<Set<string>>(new Set());
  const [loadError, setLoadError] = useState<string | null>(null);

  const pollStartedAtRef = useRef<number | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [available, conns] = await Promise.all([
        api.getAvailableToolkits(),
        api.getUserConnections(),
      ]);
      setToolkits(available);
      setConnections(conns);
      setLoadError(null);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load connectors.';
      setLoadError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Refetch when tab regains focus — covers the new-tab auth return.
  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        void refresh();
      }
    };
    document.addEventListener('visibilitychange', onVisibility);
    return () => document.removeEventListener('visibilitychange', onVisibility);
  }, [refresh]);

  // Background poll while any card is INITIATED — bounded to 10 min.
  useEffect(() => {
    const hasPending = connections.some(
      (c) => c.status === 'INITIATED' || c.status === 'INITIALIZING'
    );
    if (!hasPending) {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      pollStartedAtRef.current = null;
      return;
    }
    if (pollStartedAtRef.current === null) {
      pollStartedAtRef.current = Date.now();
    }
    if (pollTimerRef.current) return;
    pollTimerRef.current = setInterval(() => {
      const elapsed = Date.now() - (pollStartedAtRef.current ?? Date.now());
      if (elapsed > POLL_WINDOW_MS) {
        if (pollTimerRef.current) clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
        return;
      }
      void refresh();
    }, POLL_INTERVAL_MS);
    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [connections, refresh]);

  const connBySlug = new Map(connections.map((c) => [c.toolkit_slug, c]));

  const markWorking = (slug: string, on: boolean) => {
    setWorkingSlugs((prev) => {
      const next = new Set(prev);
      if (on) next.add(slug);
      else next.delete(slug);
      return next;
    });
  };

  const handleConnect = async (slug: string) => {
    // Open popup synchronously to preserve the user-gesture token. Chrome,
    // Safari, and Firefox block window.open if called after an await — the
    // user-activation is consumed by the time the fetch resolves.
    //
    // Do NOT pass 'noopener,noreferrer' here: per HTML spec, noopener makes
    // window.open return null, so we lose the handle we need to later set
    // popup.location.href. Instead we null out popup.opener after navigation
    // to get the same tamper-prevention property without losing the ref.
    const popup = window.open('about:blank', '_blank');
    markWorking(slug, true);
    try {
      const { redirect_url } = await api.connectToolkit(slug);
      if (!redirect_url) {
        // Composio returned ACTIVE — already connected. Close the popup and
        // let refresh() pick up the live state.
        if (popup) popup.close();
        toast.success('Already connected.');
      } else if (popup) {
        popup.location.href = redirect_url;
        popup.opener = null;
      } else {
        toast.error('Popup blocked. Allow popups for webwhen and try again.');
      }
      await refresh();
    } catch (err) {
      if (popup) popup.close();
      const msg = err instanceof Error ? err.message : 'Connection service unavailable.';
      toast.error(msg);
    } finally {
      markWorking(slug, false);
    }
  };

  const handleDisconnect = async (slug: string) => {
    markWorking(slug, true);
    try {
      await api.disconnectToolkit(slug);
      const displayName =
        toolkits.find((t) => t.slug === slug)?.display_name ?? slug;
      toast.success(`${displayName} disconnected.`);
      await refresh();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to disconnect.';
      toast.error(msg);
    } finally {
      markWorking(slug, false);
    }
  };

  return (
    <>
      <SettingsTabs />

      <p className={styles.helper}>
        Connections powered by Composio — you'll see their name on the
        authorization screen.{' '}
        <a
          href="https://docs.webwhen.ai/architecture/connectors-trust"
          target="_blank"
          rel="noopener noreferrer"
          className={styles.helperLink}
        >
          Privacy & security
        </a>
      </p>

      {isLoading ? (
        <div className={styles.loading}>
          <Loader2 className="w-3.5 h-3.5 animate-spin" strokeWidth={1.5} />
          Loading connectors…
        </div>
      ) : loadError ? (
        <EmptyState
          icon={Plug}
          title="Connectors unavailable"
          description={loadError}
        />
      ) : toolkits.length === 0 ? (
        <EmptyState
          icon={Plug}
          title="No connectors available"
          description="Check back soon."
        />
      ) : (
        <div className={styles.grid}>
          {toolkits.map((toolkit) => (
            <ConnectorCard
              key={toolkit.slug}
              toolkit={toolkit}
              connection={connBySlug.get(toolkit.slug) ?? null}
              onConnect={handleConnect}
              onDisconnect={handleDisconnect}
              isWorking={workingSlugs.has(toolkit.slug)}
            />
          ))}
        </div>
      )}
    </>
  );
};
