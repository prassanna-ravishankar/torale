import type { User } from '@/contexts/AuthContext';

// Gate for all connector UI surfaces until feature is cleared for GA.
// Either the build-time env flag is on, or the authed user has admin role.
export function connectorsEnabled(user: User | null): boolean {
  const envOn = import.meta.env.VITE_ENABLE_CONNECTORS === '1';
  const roleOn = user?.publicMetadata?.role === 'admin';
  return envOn || roleOn;
}
