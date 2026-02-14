import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, Trash2, ExternalLink } from 'lucide-react';
import { api } from '@/lib/api';
import { BrutalistCard } from '@/components/torale';
import { toast } from 'sonner';
import type { SlackIntegration as SlackIntegrationType, SlackChannel } from '@/types';

export const SlackIntegration: React.FC = () => {
  const [integration, setIntegration] = useState<SlackIntegrationType | null>(null);
  const [channels, setChannels] = useState<SlackChannel[]>([]);
  const [selectedChannelId, setSelectedChannelId] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingChannels, setIsLoadingChannels] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isSavingChannel, setIsSavingChannel] = useState(false);
  const [isRevoking, setIsRevoking] = useState(false);

  useEffect(() => {
    loadIntegration();
  }, []);

  const loadIntegration = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSlackIntegration();
      setIntegration(data);

      // If connected but no channel selected, load channels
      if (data.connected && !data.channel_name) {
        await loadChannels();
      }
    } catch (err: any) {
      toast.error('Failed to load Slack integration');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadChannels = async () => {
    setIsLoadingChannels(true);
    try {
      const data = await api.listSlackChannels();
      setChannels(data.channels);
    } catch (err: any) {
      toast.error('Failed to load Slack channels');
      console.error(err);
    } finally {
      setIsLoadingChannels(false);
    }
  };

  const handleConnect = async () => {
    setIsConnecting(true);
    try {
      const { authorization_url } = await api.startSlackOAuth();
      // Redirect to Slack OAuth page
      window.location.href = authorization_url;
    } catch (err: any) {
      toast.error('Failed to start Slack OAuth');
      setIsConnecting(false);
    }
    // Don't set isConnecting(false) - page will redirect
  };

  const handleSelectChannel = async () => {
    if (!selectedChannelId) {
      toast.error('Please select a channel');
      return;
    }

    const channel = channels.find(ch => ch.id === selectedChannelId);
    if (!channel) return;

    setIsSavingChannel(true);
    try {
      await api.selectSlackChannel(channel.id, channel.name);
      toast.success(`Channel ${channel.name} selected`);
      await loadIntegration();
    } catch (err: any) {
      toast.error('Failed to select channel');
    } finally {
      setIsSavingChannel(false);
    }
  };

  const handleRevoke = async () => {
    if (!confirm('Are you sure you want to disconnect Slack? You will stop receiving notifications.')) {
      return;
    }

    setIsRevoking(true);
    try {
      await api.revokeSlackIntegration();
      toast.success('Slack integration disconnected');
      setIntegration({ connected: false });
      setChannels([]);
      setSelectedChannelId('');
    } catch (err: any) {
      toast.error('Failed to revoke integration');
    } finally {
      setIsRevoking(false);
    }
  };

  if (isLoading) {
    return (
      <BrutalistCard className="p-8 flex items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
      </BrutalistCard>
    );
  }

  const isConnected = integration?.connected ?? false;

  return (
    <BrutalistCard>
      {/* Header */}
      <div className="p-4 border-b border-zinc-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Slack Logo */}
          <div className="w-8 h-8 bg-[#4A154B] flex items-center justify-center">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="white">
              <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
            </svg>
          </div>
          <div>
            <p className="text-sm font-mono font-semibold text-zinc-900">Slack</p>
            <p className="text-[10px] text-zinc-500">Send notifications to Slack channels</p>
          </div>
        </div>
        {isConnected && (
          <span className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-mono uppercase tracking-wider border bg-emerald-50 text-emerald-700 border-emerald-200">
            <CheckCircle2 className="h-3 w-3" />
            Connected
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {!isConnected ? (
          // Not connected - show connect button
          <div className="text-center py-6">
            <p className="text-xs text-zinc-500 mb-4">
              Connect your Slack workspace to receive notifications directly in Slack channels.
            </p>
            <button
              onClick={handleConnect}
              disabled={isConnecting}
              className="inline-flex items-center gap-2 px-6 py-3 bg-[#4A154B] text-white text-sm font-mono hover:bg-[#611f69] transition-colors disabled:opacity-50"
            >
              {isConnecting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ExternalLink className="h-4 w-4" />
              )}
              Connect to Slack
            </button>
          </div>
        ) : (
          // Connected - show workspace info and channel selection
          <>
            {/* Workspace Info */}
            <div className="space-y-2">
              <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                Workspace
              </label>
              <div className="flex items-center justify-between px-3 py-2 bg-zinc-50 border border-zinc-200">
                <span className="text-sm font-mono text-zinc-900">{integration.workspace_name}</span>
                <span className="text-[10px] text-zinc-400 font-mono">
                  Connected {new Date(integration.connected_at!).toLocaleDateString()}
                </span>
              </div>
            </div>

            {/* Channel Selection */}
            {integration.channel_name ? (
              // Channel already selected
              <div className="space-y-2">
                <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                  Notification Channel
                </label>
                <div className="flex items-center justify-between px-3 py-2 bg-emerald-50 border border-emerald-200">
                  <span className="text-sm font-mono text-emerald-900">{integration.channel_name}</span>
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                </div>
                {integration.last_used_at && (
                  <p className="text-[10px] text-zinc-400 font-mono">
                    Last notification sent {new Date(integration.last_used_at).toLocaleString()}
                  </p>
                )}
              </div>
            ) : (
              // Select channel
              <div className="space-y-2">
                <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
                  Select Notification Channel
                </label>
                {isLoadingChannels ? (
                  <div className="flex items-center justify-center p-4">
                    <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
                  </div>
                ) : (
                  <div className="flex flex-col sm:flex-row gap-2">
                    <select
                      value={selectedChannelId}
                      onChange={(e) => setSelectedChannelId(e.target.value)}
                      disabled={isSavingChannel}
                      className="flex-1 px-3 py-2 bg-white border-2 border-zinc-200 text-sm font-mono focus:outline-none focus:border-zinc-900 disabled:opacity-50"
                    >
                      <option value="">Choose a channel...</option>
                      {channels.map((channel) => (
                        <option key={channel.id} value={channel.id}>
                          {channel.name}
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={handleSelectChannel}
                      disabled={isSavingChannel || !selectedChannelId}
                      className="px-4 py-2 bg-zinc-900 text-white text-sm font-mono hover:bg-[hsl(10,90%,55%)] transition-colors disabled:opacity-50 disabled:hover:bg-zinc-900 shrink-0"
                    >
                      {isSavingChannel ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Disconnect Button */}
            <button
              onClick={handleRevoke}
              disabled={isRevoking}
              className="w-full flex items-center justify-center gap-2 p-3 border-2 border-dashed border-zinc-300 text-zinc-600 hover:border-red-500 hover:text-red-600 transition-all text-sm font-mono disabled:opacity-50"
            >
              {isRevoking ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              Disconnect Slack
            </button>
          </>
        )}
      </div>
    </BrutalistCard>
  );
};
