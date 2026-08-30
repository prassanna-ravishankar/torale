import React, { useState, useEffect, useCallback } from 'react';
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
  DialogTitle,
} from '@/components/ui/dialog';
import { Loader2, Plus, Trash2, Copy, CheckCircle2, ShieldAlert } from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import { getErrorMessage } from '@/lib/utils';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import type { ApiKey } from '@/types';
import { StatusBadge } from '@/components/torale';
import styles from './Settings.module.css';
import modalStyles from '@/components/ui/modal/Modal.module.css';

export const ApiKeyManagementSection: React.FC = () => {
  const api = useApi();
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

  const loadApiKeys = useCallback(async () => {
    setIsLoading(true);
    try {
      const keys = await api.getApiKeys();
      setApiKeys(keys);
    } catch (err) {
      toast.error('Failed to load API keys');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [api]);

  useEffect(() => {
    if (isDeveloper) {
      void loadApiKeys();
    } else {
      setIsLoading(false);
    }
  }, [isDeveloper, loadApiKeys]);

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
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to create API key'));
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
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to revoke API key'));
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
      <div className={styles.emptyHint} style={{ textAlign: 'left' }}>
        <div className="flex items-start gap-2">
          <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" style={{ color: 'var(--ww-warn)' }} />
          <span>
            API keys are a developer feature. Contact support to request developer access for
            programmatic SDK use.
          </span>
        </div>
      </div>
    );
  }

  const activeKeys = apiKeys.filter((k) => k.is_active);
  const revokedKeys = apiKeys.filter((k) => !k.is_active);

  return (
    <>
      {isLoading ? (
        <div className={styles.loadingRow}>
          <Loader2 className="h-4 w-4 animate-spin" />
          loading…
        </div>
      ) : (
        <>
          <div className={styles.actions} style={{ marginBottom: 12 }}>
            <button
              type="button"
              onClick={handleCreateClick}
              disabled={isCreating}
              className={styles.btnPrimary}
            >
              <Plus className="h-3.5 w-3.5" />
              Create API key
            </button>
          </div>

          {activeKeys.length === 0 && revokedKeys.length === 0 ? (
            <div className={styles.emptyHint}>
              No API keys yet. Create one for programmatic access.
            </div>
          ) : (
            <div className={styles.runs}>
              {activeKeys.map((key) => (
                <div key={key.id} className={styles.run}>
                  <span className={styles.runT}>{formatDate(key.created_at)}</span>
                  <span className={`${styles.runDot} ${styles.runDotSuccess}`} />
                  <span className={`${styles.runB} ${styles.runBStrong}`}>
                    {key.name}{' '}
                    <span style={{ color: 'var(--ww-ink-4)', marginLeft: 6 }}>{key.key_prefix}</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    <StatusBadge variant="active" size="sm" />
                    <button
                      type="button"
                      onClick={() => handleRevokeClick(key)}
                      disabled={!!isRevoking}
                      className={`${styles.iconBtn} ${styles.iconBtnDanger}`}
                      aria-label={`Revoke ${key.name}`}
                    >
                      {isRevoking === key.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </button>
                  </span>
                </div>
              ))}
              {revokedKeys.map((key) => (
                <div key={key.id} className={styles.run}>
                  <span className={styles.runT}>{formatDate(key.created_at)}</span>
                  <span className={styles.runDot} />
                  <span className={`${styles.runB} ${styles.runBMuted}`}>
                    {key.name}{' '}
                    <span style={{ marginLeft: 6 }}>{key.key_prefix}</span>
                  </span>
                  <StatusBadge variant="failed" label="Revoked" size="sm" />
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Create API Key Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className={modalStyles.modal}>
          <DialogTitle className="sr-only">Create API key</DialogTitle>
          <DialogDescription className="sr-only">
            Create a new API key for programmatic access.
          </DialogDescription>

          <div className={modalStyles.head}>
            <span className={modalStyles.headTitle}>create api key</span>
            <button
              type="button"
              className={modalStyles.headClose}
              onClick={() => setShowCreateDialog(false)}
              aria-label="Close"
            >
              ×
            </button>
          </div>

          <div className={modalStyles.body}>
            <div className={styles.field}>
              <label htmlFor="api-key-name">Key name</label>
              <input
                id="api-key-name"
                placeholder="e.g., Development key"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateKey()}
                autoFocus
              />
            </div>
          </div>

          <div className={modalStyles.foot}>
            <span className={modalStyles.footHint}>shown once after creation</span>
            <div className={modalStyles.footActions}>
              <button
                type="button"
                onClick={() => setShowCreateDialog(false)}
                disabled={isCreating}
                className={styles.btnGhost}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreateKey}
                disabled={isCreating || !newKeyName.trim()}
                className={styles.btnPrimary}
              >
                {isCreating && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                {isCreating ? 'Creating…' : 'Create'}
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Created Key Dialog (one-time display) */}
      <Dialog open={showCreatedKeyDialog} onOpenChange={setShowCreatedKeyDialog}>
        <DialogContent className={modalStyles.modal}>
          <DialogTitle className="sr-only">API key created</DialogTitle>
          <DialogDescription className="sr-only">
            Save this key securely. It will not be shown again.
          </DialogDescription>

          <div className={modalStyles.head}>
            <span className={modalStyles.headTitle}>api key created</span>
            <button
              type="button"
              className={modalStyles.headClose}
              onClick={() => {
                setShowCreatedKeyDialog(false);
                setCreatedKey(null);
              }}
              aria-label="Close"
            >
              ×
            </button>
          </div>

          <div className={modalStyles.body}>
            <div className={styles.disclosure}>
              <div className={styles.disclosureWarn}>
                <ShieldAlert className="h-4 w-4 shrink-0" />
                This is the only time you'll see this key. Copy it now and store it securely.
              </div>
              <div className="flex gap-2 items-stretch">
                <div className={styles.secret} style={{ wordBreak: 'break-all', whiteSpace: 'normal' }}>
                  <code style={{ whiteSpace: 'normal', overflow: 'visible' }}>{createdKey}</code>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopyKey(createdKey || '')}
                  className={styles.btnSecondary}
                  style={{ alignSelf: 'flex-start' }}
                >
                  {keyToCopy === createdKey ? (
                    <>
                      <CheckCircle2 className="h-3.5 w-3.5" style={{ color: 'var(--ww-success)' }} />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      Copy
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className={modalStyles.foot}>
            <span className={modalStyles.footHint}>store securely · cannot be recovered</span>
            <div className={modalStyles.footActions}>
              <button
                type="button"
                onClick={() => {
                  setShowCreatedKeyDialog(false);
                  setCreatedKey(null);
                }}
                className={styles.btnPrimary}
              >
                Done
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Revoke Confirmation Dialog */}
      <AlertDialog open={!!keyToRevoke} onOpenChange={() => setKeyToRevoke(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke API key?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently revoke "<strong className="font-mono">{keyToRevoke?.name}</strong>".
              Any applications using this key will no longer be able to access your account.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className={styles.btnSecondary}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmRevoke}
              className={styles.btnDanger}
            >
              Revoke
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
