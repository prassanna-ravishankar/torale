import React, { useState, useEffect } from 'react';
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Loader2, Key, Plus, Trash2, Copy, CheckCircle2, ShieldAlert } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import type { ApiKey } from '@/types';

export const ApiKeyManagementSection: React.FC = () => {
  const { user } = useAuth();
  const userRole = user?.publicMetadata?.role as string | undefined;
  const isDeveloper = userRole === 'developer' || userRole === 'admin';

  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [isRevoking, setIsRevoking] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showCreatedKeyDialog, setShowCreatedKeyDialog] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [keyToCopy, setKeyToCopy] = useState<string | null>(null);
  const [keyToRevoke, setKeyToRevoke] = useState<ApiKey | null>(null);

  useEffect(() => {
    if (isDeveloper) {
      loadApiKeys();
    } else {
      setIsLoading(false);
    }
  }, [isDeveloper]);

  const loadApiKeys = async () => {
    setIsLoading(true);
    try {
      const keys = await api.getApiKeys();
      setApiKeys(keys);
    } catch (err: any) {
      toast.error('Failed to load API keys');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateClick = () => {
    setNewKeyName('');
    setShowCreateDialog(true);
  };

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      toast.error('Please enter a key name');
      return;
    }

    setIsCreating(true);
    try {
      const response = await api.createApiKey(newKeyName.trim());
      setCreatedKey(response.key);
      await loadApiKeys();
      setShowCreateDialog(false);
      setShowCreatedKeyDialog(true);
      toast.success('API key created successfully');
    } catch (err: any) {
      toast.error(err.message || 'Failed to create API key');
    } finally {
      setIsCreating(false);
    }
  };

  const handleCopyKey = async (key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setKeyToCopy(key);
      toast.success('API key copied to clipboard');
      setTimeout(() => setKeyToCopy(null), 2000);
    } catch (err) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const handleRevokeClick = (key: ApiKey) => {
    setKeyToRevoke(key);
  };

  const handleConfirmRevoke = async () => {
    if (!keyToRevoke) return;

    setIsRevoking(keyToRevoke.id);
    try {
      await api.revokeApiKey(keyToRevoke.id);
      await loadApiKeys();
      toast.success('API key revoked successfully');
    } catch (err: any) {
      toast.error(err.message || 'Failed to revoke API key');
    } finally {
      setIsRevoking(null);
      setKeyToRevoke(null);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (!isDeveloper) {
    return (
      <div className="bg-white border-2 border-zinc-200">
        <div className="p-4 border-b border-zinc-200">
          <p className="text-xs text-zinc-500">
            Programmatic access to Torale API via Python SDK
          </p>
        </div>
        <div className="p-6 flex items-start gap-3 bg-amber-50 border-t-2 border-amber-200">
          <ShieldAlert className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-mono text-amber-900">Developer Access Required</p>
            <p className="text-xs text-amber-700 mt-1">
              API keys allow programmatic access via the Python SDK. Contact support to request developer access.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const activeKey = apiKeys.find((k) => k.is_active);

  return (
    <>
      <div className="bg-white border-2 border-zinc-200">
        {/* Header */}
        <div className="p-4 border-b border-zinc-200">
          <p className="text-xs text-zinc-500">
            Manage API keys for programmatic access via the Python SDK.
          </p>
        </div>

        {/* Content */}
        <div className="p-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-zinc-400" />
            </div>
          ) : (
            <div className="space-y-3">
              {/* Active API Key */}
              {activeKey ? (
                <>
                  <div className="p-3 bg-zinc-50 border border-zinc-200">
                    <div className="flex items-start gap-3">
                      <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center shrink-0">
                        <Key className="h-4 w-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <code className="text-xs sm:text-sm font-mono text-zinc-900 break-all">{activeKey.key_prefix}</code>
                            <p className="text-[10px] font-mono text-zinc-500 mt-0.5">
                              {activeKey.name} • Created {formatDate(activeKey.created_at)}
                            </p>
                          </div>
                          <button
                            onClick={() => handleRevokeClick(activeKey)}
                            disabled={!!isRevoking}
                            className="p-1.5 text-zinc-400 hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50 shrink-0"
                          >
                            {isRevoking === activeKey.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </button>
                        </div>
                        <div className="flex flex-wrap items-center gap-1.5 mt-2">
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-700 text-[9px] font-mono uppercase tracking-wider border border-emerald-200">
                            <CheckCircle2 className="h-3 w-3" />
                            Active
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* SDK Install Hint */}
                  <div className="p-3 bg-zinc-900 text-zinc-300 font-mono text-xs">
                    <span className="text-zinc-500">$</span> pip install torale
                  </div>
                </>
              ) : (
                <div className="text-center py-6">
                  <div className="bg-zinc-100 w-12 h-12 flex items-center justify-center mx-auto mb-3">
                    <Key className="h-6 w-6 text-zinc-400" />
                  </div>
                  <p className="text-xs text-zinc-500 font-mono mb-4">
                    No active API key. Generate one to use the Python SDK.
                  </p>
                  <button
                    onClick={handleCreateClick}
                    disabled={isCreating}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-900 text-white text-sm font-mono hover:bg-[hsl(10,90%,55%)] transition-colors disabled:opacity-50"
                  >
                    <Plus className="h-4 w-4" />
                    Generate API Key
                  </button>
                </div>
              )}

              {/* Revoked Keys (if any) */}
              {apiKeys.filter((k) => !k.is_active).length > 0 && (
                <div className="space-y-2 pt-3 border-t border-zinc-200">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">Revoked Keys</p>
                  {apiKeys
                    .filter((k) => !k.is_active)
                    .map((key) => (
                      <div
                        key={key.id}
                        className="flex items-center gap-3 p-2 border border-dashed border-zinc-200 opacity-50"
                      >
                        <Key className="h-4 w-4 text-zinc-400" />
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <code className="text-xs font-mono text-zinc-500">{key.key_prefix}</code>
                            <span className="px-1.5 py-0.5 bg-zinc-100 text-zinc-500 text-[9px] font-mono uppercase tracking-wider">
                              Revoked
                            </span>
                          </div>
                          <p className="text-[10px] text-zinc-400">{key.name}</p>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create API Key Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="border-2 border-zinc-900">
          <DialogHeader>
            <DialogTitle className="font-grotesk">Generate API Key</DialogTitle>
            <DialogDescription className="text-zinc-600">
              Create a new API key for programmatic access to your Torale account.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-4">
            <label className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
              Key Name
            </label>
            <input
              placeholder="e.g., Development Key"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateKey()}
              className="w-full px-3 py-2 border-2 border-zinc-200 text-sm font-mono focus:outline-none focus:border-zinc-900"
            />
          </div>
          <DialogFooter>
            <button
              onClick={() => setShowCreateDialog(false)}
              disabled={isCreating}
              className="px-4 py-2 border border-zinc-200 text-zinc-600 text-sm font-mono hover:border-zinc-400 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateKey}
              disabled={isCreating || !newKeyName.trim()}
              className="px-4 py-2 bg-zinc-900 text-white text-sm font-mono hover:bg-[hsl(10,90%,55%)] transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isCreating && <Loader2 className="h-4 w-4 animate-spin" />}
              {isCreating ? 'Generating...' : 'Generate Key'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Show Created Key Dialog (One-time display) */}
      <Dialog open={showCreatedKeyDialog} onOpenChange={setShowCreatedKeyDialog}>
        <DialogContent className="border-2 border-zinc-900">
          <DialogHeader>
            <DialogTitle className="font-grotesk">API Key Created</DialogTitle>
            <DialogDescription className="text-zinc-600">
              Save this key securely. You won't be able to see it again!
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-3 bg-red-50 border-2 border-red-200 text-red-700 text-xs font-mono">
              This is the only time you'll see this key. Copy it now and store it securely.
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="flex-1 px-3 py-2 bg-zinc-900 text-zinc-300 font-mono text-[10px] sm:text-sm border-2 border-zinc-900 break-all min-w-0">
                {createdKey}
              </div>
              <button
                onClick={() => handleCopyKey(createdKey || '')}
                className="p-2 border-2 border-zinc-200 text-zinc-600 hover:border-zinc-900 hover:text-zinc-900 transition-colors shrink-0 self-start"
              >
                {keyToCopy === createdKey ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
          <DialogFooter>
            <button
              onClick={() => {
                setShowCreatedKeyDialog(false);
                setCreatedKey(null);
              }}
              className="px-4 py-2 bg-zinc-900 text-white text-sm font-mono hover:bg-[hsl(10,90%,55%)] transition-colors"
            >
              Done
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Revoke Confirmation Dialog */}
      <AlertDialog open={!!keyToRevoke} onOpenChange={() => setKeyToRevoke(null)}>
        <AlertDialogContent className="border-2 border-zinc-900">
          <AlertDialogHeader>
            <AlertDialogTitle className="font-grotesk">Revoke API Key?</AlertDialogTitle>
            <AlertDialogDescription className="text-zinc-600">
              This will permanently revoke the API key "<strong className="font-mono">{keyToRevoke?.name}</strong>".
              Any applications using this key will no longer be able to access your account.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="font-mono text-sm">Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmRevoke}
              className="bg-red-600 hover:bg-red-700 font-mono text-sm"
            >
              Revoke Key
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
