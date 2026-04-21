import React, { useState } from 'react';
import { Loader2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import api from '@/lib/api';

interface ReconnectButtonProps {
  toolkitSlug: string;
  displayName: string;
  size?: 'sm' | 'default';
  className?: string;
}

// One-click reconnect. Kicks the Composio redirect in a new tab.
// Shared by ConnectorCard (expired state) and task-detail degradation banner.
export const ReconnectButton: React.FC<ReconnectButtonProps> = ({
  toolkitSlug,
  displayName,
  size = 'sm',
  className,
}) => {
  const [isWorking, setIsWorking] = useState(false);

  const handleClick = async () => {
    // Open popup synchronously to preserve the user-gesture token. Browsers
    // block window.open after an await because user-activation is consumed.
    const popup = window.open('about:blank', '_blank', 'noopener,noreferrer');
    setIsWorking(true);
    try {
      const { redirect_url } = await api.connectToolkit(toolkitSlug);
      if (popup) {
        popup.location.href = redirect_url;
      } else {
        toast.error('Popup blocked. Allow popups for Torale and try again.');
      }
    } catch (err) {
      if (popup) popup.close();
      const msg = err instanceof Error ? err.message : 'Connection service unavailable.';
      toast.error(`Couldn't reconnect ${displayName}: ${msg}`);
    } finally {
      setIsWorking(false);
    }
  };

  return (
    <Button size={size} onClick={handleClick} disabled={isWorking} className={className}>
      {isWorking ? (
        <Loader2 className="w-3 h-3 animate-spin" />
      ) : (
        <>
          <RefreshCw className="w-3 h-3 mr-1" /> Reconnect
        </>
      )}
    </Button>
  );
};
