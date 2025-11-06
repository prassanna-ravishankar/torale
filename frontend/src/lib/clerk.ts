import { Clerk } from '@clerk/clerk-js';
import { writable, derived, get } from 'svelte/store';
import { api } from './apiClient';

// Read Clerk key from runtime config (injected by Kubernetes)
const CLERK_PUBLISHABLE_KEY = (window as any).CONFIG?.clerkPublishableKey || import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!CLERK_PUBLISHABLE_KEY) {
  throw new Error('Missing Clerk Publishable Key');
}

// Initialize Clerk
const clerk = new Clerk(CLERK_PUBLISHABLE_KEY);

// Stores
export const clerkLoaded = writable(false);
export const clerkUser = writable<any>(null);
export const clerkSession = writable<any>(null);

export const isSignedIn = derived(
  [clerkUser, clerkSession],
  ([$user, $session]) => !!$user && !!$session
);

// Initialize Clerk
export async function initializeClerk() {
  try {
    await clerk.load();
    clerkLoaded.set(true);

    // Update stores when Clerk state changes
    clerk.addListener((clerk) => {
      clerkUser.set(clerk.user);
      clerkSession.set(clerk.session);

      // Set up API token getter when session is available
      if (clerk.session) {
        api.setTokenGetter(() => clerk.session?.getToken() || Promise.resolve(null));
      }
    });

    // Initial update
    clerkUser.set(clerk.user);
    clerkSession.set(clerk.session);

    // Set up API token getter
    if (clerk.session) {
      api.setTokenGetter(() => clerk.session?.getToken() || Promise.resolve(null));
    }
  } catch (error) {
    console.error('Failed to initialize Clerk:', error);
  }
}

// Export clerk instance for components
export { clerk };

// Helper functions
export function openSignIn() {
  clerk.openSignIn({ routing: 'hash' });
}

export function openSignUp() {
  clerk.openSignUp({ routing: 'hash' });
}

export function signOut() {
  return clerk.signOut();
}

export function getToken() {
  return clerk.session?.getToken() || Promise.resolve(null);
}
