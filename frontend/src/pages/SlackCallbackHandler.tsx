import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

/**
 * Handles Slack OAuth callback and redirects back to settings
 */
export const SlackCallbackHandler: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    const success = searchParams.get('success');
    const workspace = searchParams.get('workspace');
    const error = searchParams.get('error');

    if (error) {
      toast.error(`Slack authorization failed: ${error}`);
      setStatus('error');
      setTimeout(() => navigate('/settings/notifications'), 2000);
      return;
    }

    if (success === 'true' && workspace) {
      toast.success(`Slack connected to ${workspace}! Select a channel to complete setup.`);
      setStatus('success');
      setTimeout(() => navigate('/settings/notifications'), 1500);
      return;
    }

    // Invalid callback
    toast.error('Invalid OAuth callback');
    setStatus('error');
    setTimeout(() => navigate('/settings/notifications'), 2000);
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center">
      <div className="bg-white border-2 border-zinc-900 p-8 max-w-md w-full mx-4">
        <div className="text-center space-y-4">
          {status === 'loading' && (
            <>
              <Loader2 className="h-12 w-12 animate-spin text-zinc-400 mx-auto" />
              <h2 className="text-xl font-bold font-grotesk">Connecting to Slack...</h2>
              <p className="text-sm text-zinc-500 font-mono">Please wait</p>
            </>
          )}
          {status === 'success' && (
            <>
              <CheckCircle2 className="h-12 w-12 text-emerald-600 mx-auto" />
              <h2 className="text-xl font-bold font-grotesk">Connected!</h2>
              <p className="text-sm text-zinc-500 font-mono">Redirecting to settings...</p>
            </>
          )}
          {status === 'error' && (
            <>
              <AlertCircle className="h-12 w-12 text-red-600 mx-auto" />
              <h2 className="text-xl font-bold font-grotesk">Connection Failed</h2>
              <p className="text-sm text-zinc-500 font-mono">Redirecting to settings...</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
