import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, type MockedFunction } from 'vitest';
import Navigation from './Navigation';
import { usePathname } from 'next/navigation';
import { useAuth, type AuthContextType } from '@/contexts/AuthContext';
import type { User, Session, AuthError } from '@supabase/supabase-js';

// Mock supabaseClient
vi.mock('@/lib/supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null }, error: null }),
      onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
      // Add other auth methods if they are called directly or indirectly by AuthContext during render
      // For Navigation.test.tsx, these two are the most likely to be involved via AuthProvider initialization
    },
    // Add other supabase services if needed (e.g., from)
  },
}));

// Mock next/navigation
vi.mock('next/navigation', async (importOriginal) => {
  const actual = await importOriginal<typeof import('next/navigation')>();
  return {
    ...actual,
    usePathname: vi.fn(),
  };
});

// Mock AuthContext
vi.mock('@/contexts/AuthContext', async (importOriginal) => {
  // We need to import the actual useAuth to be able to mock it effectively
  // but also need to ensure that AuthProvider within it doesn't run its real useEffect logic
  // The mock of supabaseClient should prevent errors, but this ensures useAuth is what we control.
  const actual = await importOriginal<typeof import('@/contexts/AuthContext')>();
  return {
    ...actual, // Spread actual to keep AuthProvider export if needed elsewhere, though not directly used in this test
    useAuth: vi.fn(), // This is the function we will mock the return value of
  };
});

// Use imported MockedFunction type
const mockUseAuth = useAuth as MockedFunction<typeof useAuth>;
const mockUsePathname = usePathname as MockedFunction<typeof usePathname>;

// Helper to create a full AuthContextType mock for cleaner tests
const createMockAuthContextValue = (userValue: User | null, signOutFn: () => Promise<void> = vi.fn()): AuthContextType => ({
  user: userValue,
  session: null, // Provide a default or mock if needed by component
  loading: false, // Provide a default
  signIn: vi.fn().mockResolvedValue({ error: null, session: null as Session | null }),
  signUp: vi.fn().mockResolvedValue({ error: null as AuthError | null }),
  signOut: signOutFn,
  signInWithMagicLink: vi.fn().mockResolvedValue({ error: null as AuthError | null }),
  refreshSession: vi.fn().mockResolvedValue(false),
});

describe('Navigation Component', () => {
  beforeEach(() => {
    vi.clearAllMocks(); // Clear all mocks, including supabaseClient mocks
    // Reset specific hook mocks that we control directly
    mockUsePathname.mockReset();
    mockUseAuth.mockReset();
  });

  it('renders basic navigation links', () => {
    mockUsePathname.mockReturnValue('/');
    mockUseAuth.mockReturnValue(createMockAuthContextValue(null));

    render(<Navigation />);

    expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /alerts/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /settings/i })).toBeInTheDocument();
  });

  it('renders "Sign In" link when user is not authenticated', () => {
    mockUsePathname.mockReturnValue('/');
    mockUseAuth.mockReturnValue(createMockAuthContextValue(null));

    render(<Navigation />);

    expect(screen.getByRole('link', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /profile/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /sign out/i })).not.toBeInTheDocument();
  });

  it('renders "Profile" link and "Sign Out" button when user is authenticated', () => {
    const mockSignOutFn = vi.fn().mockResolvedValue(undefined);
    mockUsePathname.mockReturnValue('/');
    mockUseAuth.mockReturnValue(createMockAuthContextValue(
      { id: '123', email: 'test@example.com' } as User, 
      mockSignOutFn
    ));

    render(<Navigation />);

    expect(screen.getByRole('link', { name: /profile/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /sign in/i })).not.toBeInTheDocument();
  });

  // TODO: Add test for active link styling
  // TODO: Add test for signOut button click
}); 