import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Loader2, Plug } from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';
import type { AvailableToolkit, UserConnection } from '@/types';
import { EmptyState } from '@/components/torale';
import { SettingsTabs } from '@/components/settings/SettingsTabs';
import { ConnectorCard } from '@/components/connectors/ConnectorCard';

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
    markWorking(slug, true);
    try {
      const { redirect_url } = await api.connectToolkit(slug);
      window.open(redirect_url, '_blank', 'noopener,noreferrer');
      await refresh();
    } catch (err) {
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
    <div className="min-h-screen bg-zinc-50">
      <main className="p-4 md:p-8 max-w-6xl mx-auto">
        <header className="mb-6">
          <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono mb-2">
            <Link to="/dashboard" className="hover:text-zinc-900 transition-colors">
              Dashboard
            </Link>
            <span>/</span>
            <span className="text-zinc-900">Settings</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-zinc-900 text-white w-10 h-10 flex items-center justify-center">
              <Plug className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold font-grotesk tracking-tight">
                Connectors
              </h1>
              <p className="text-sm text-zinc-500 font-mono">
                Let the agent reach into your tools
              </p>
            </div>
          </div>
        </header>

        <SettingsTabs />

        <p className="text-xs text-zinc-400 font-mono mb-6">
          Connections powered by Composio — you'll see their name on the
          authorization screen.
        </p>

        {isLoading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
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
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
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
      </main>
    </div>
  );
};
