import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
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
import { Loader2, Key, Plus, Trash2, Copy, CheckCircle2, AlertCircle, ShieldAlert } from 'lucide-react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { useUser } from '@clerk/clerk-react';
import type { ApiKey } from '@/types';

export const ApiKeyManagementSection: React.FC = () => {
  const { user: clerkUser } = useUser();
  const userRole = clerkUser?.publicMetadata?.role as string | undefined;
  const isDeveloper = userRole === 'developer';

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
      setApiKeys((prev) => [...prev, response.key_info]);
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
      setApiKeys((prev) => prev.map((k) => (k.id === keyToRevoke.id ? { ...k, is_active: false } : k)));
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
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!isDeveloper) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>API Access</CardTitle>
          <CardDescription>Programmatic access to Torale API via Python SDK</CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <ShieldAlert className="h-4 w-4" />
            <AlertDescription>
              Developer access required. API keys allow programmatic access to your Torale account via the
              Python SDK. Contact support to request developer access.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const activeKey = apiKeys.find((k) => k.is_active);

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>API Access</CardTitle>
          <CardDescription>
            Manage your API key for programmatic access via the Python SDK. You can have one active key at a
            time.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {/* Active API Key */}
              {activeKey ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div className="flex items-center gap-3">
                      <div className="rounded-full bg-primary/10 p-2">
                        <Key className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-mono text-sm">{activeKey.key_prefix}</p>
                          <Badge variant="default" className="h-5">
                            Active
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{activeKey.name}</p>
                        <p className="text-xs text-muted-foreground">
                          Created {formatDate(activeKey.created_at)}
                          {activeKey.last_used_at && ` • Last used ${formatDate(activeKey.last_used_at)}`}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRevokeClick(activeKey)}
                      disabled={!!isRevoking}
                    >
                      {isRevoking === activeKey.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Trash2 className="h-4 w-4 mr-2" />
                          Revoke
                        </>
                      )}
                    </Button>
                  </div>

                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      Use this API key with the Torale Python SDK to manage tasks programmatically. Install
                      with: <code className="font-mono text-xs">pip install torale</code>
                    </AlertDescription>
                  </Alert>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="rounded-full bg-muted p-3 w-fit mx-auto mb-4">
                    <Key className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground mb-4">
                    No active API key. Generate one to use the Python SDK.
                  </p>
                  <Button onClick={handleCreateClick} disabled={isCreating}>
                    <Plus className="h-4 w-4 mr-2" />
                    Generate API Key
                  </Button>
                </div>
              )}

              {/* Revoked Keys (if any) */}
              {apiKeys.filter((k) => !k.is_active).length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-muted-foreground">Revoked Keys</h4>
                  {apiKeys
                    .filter((k) => !k.is_active)
                    .map((key) => (
                      <div
                        key={key.id}
                        className="flex items-center justify-between rounded-lg border border-dashed p-3 opacity-60"
                      >
                        <div className="flex items-center gap-3">
                          <Key className="h-4 w-4 text-muted-foreground" />
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-mono text-sm">{key.key_prefix}</p>
                              <Badge variant="secondary" className="h-5">
                                Revoked
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">{key.name}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Create API Key Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Generate API Key</DialogTitle>
            <DialogDescription>
              Create a new API key for programmatic access to your Torale account.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="key-name">Key Name</Label>
              <Input
                id="key-name"
                placeholder="e.g., Development Key"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreateKey()}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)} disabled={isCreating}>
              Cancel
            </Button>
            <Button onClick={handleCreateKey} disabled={isCreating || !newKeyName.trim()}>
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>Generate Key</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Show Created Key Dialog (One-time display) */}
      <Dialog open={showCreatedKeyDialog} onOpenChange={setShowCreatedKeyDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>API Key Created</DialogTitle>
            <DialogDescription>
              Save this key securely. You won't be able to see it again!
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                This is the only time you'll see this key. Copy it now and store it securely.
              </AlertDescription>
            </Alert>
            <div className="flex items-center gap-2">
              <Input value={createdKey || ''} readOnly className="font-mono text-sm" />
              <Button
                variant="outline"
                size="icon"
                onClick={() => handleCopyKey(createdKey || '')}
                className="shrink-0"
              >
                {keyToCopy === createdKey ? (
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
          <DialogFooter>
            <Button
              onClick={() => {
                setShowCreatedKeyDialog(false);
                setCreatedKey(null);
              }}
            >
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Revoke Confirmation Dialog */}
      <AlertDialog open={!!keyToRevoke} onOpenChange={() => setKeyToRevoke(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke API Key?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently revoke the API key "{keyToRevoke?.name}". Any applications using this
              key will no longer be able to access your account.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmRevoke} className="bg-destructive text-destructive-foreground">
              Revoke Key
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};
