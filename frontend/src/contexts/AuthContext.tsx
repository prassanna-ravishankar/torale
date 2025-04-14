"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { User, AuthError, Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signIn: (
    email: string,
    password: string,
  ) => Promise<{ error: AuthError | null; session: Session | null }>;
  signUp: (
    email: string,
    password: string,
  ) => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<void>;
  signInWithMagicLink: (email: string) => Promise<{ error: AuthError | null }>;
  refreshSession: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log("AuthProvider: Initializing auth state");

    // Check active sessions and sets the user
    const initializeAuth = async () => {
      try {
        const {
          data: { session: initialSession },
        } = await supabase.auth.getSession();
        console.log("AuthProvider: Initial session check:", !!initialSession);

        if (initialSession) {
          setSession(initialSession);
          setUser(initialSession.user);
          console.log(
            "AuthProvider: User set from session:",
            initialSession.user.email,
          );
          console.log(
            "AuthProvider: Session expires at:",
            new Date(initialSession.expires_at! * 1000).toISOString(),
          );
        } else {
          setSession(null);
          setUser(null);
          console.log("AuthProvider: No initial session found");
        }
      } catch (error) {
        console.error("AuthProvider: Error getting session:", error);
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();

    // Listen for changes on auth state
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, currentSession) => {
      console.log(`AuthProvider: Auth state changed (${event})`);

      if (currentSession) {
        setSession(currentSession);
        setUser(currentSession.user);
        console.log("AuthProvider: User updated:", currentSession.user.email);
        console.log("AuthProvider: Session data:", {
          expires_at: currentSession.expires_at
            ? new Date(currentSession.expires_at * 1000).toISOString()
            : "unknown",
          has_access_token: !!currentSession.access_token,
          has_refresh_token: !!currentSession.refresh_token,
        });
      } else {
        setSession(null);
        setUser(null);
        console.log("AuthProvider: User cleared (no session)");
      }

      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    console.log("AuthProvider: Signing in with email/password:", email);

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error(
          "AuthProvider: Sign-in error:",
          error.message,
          error.status,
        );
        return { error, session: null };
      }

      if (!data.session) {
        console.error(
          "AuthProvider: Sign-in succeeded but no session was returned",
        );
        return {
          error: {
            message: "Authentication succeeded but no session was established",
            status: 500,
          } as AuthError,
          session: null,
        };
      }

      console.log("AuthProvider: Sign-in successful, session established");
      console.log(
        "AuthProvider: Session expires at:",
        new Date(data.session.expires_at! * 1000).toISOString(),
      );

      return { error: null, session: data.session };
    } catch (error) {
      console.error("AuthProvider: Unexpected error during sign-in:", error);
      return {
        error: {
          message: "An unexpected error occurred",
          status: 500,
        } as AuthError,
        session: null,
      };
    }
  };

  const signUp = async (email: string, password: string) => {
    console.log("AuthProvider: Signing up with email:", email);

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (error) {
        console.error(
          "AuthProvider: Sign-up error:",
          error.message,
          error.status,
        );
        return { error };
      }

      console.log(
        "AuthProvider: Sign-up successful. Email confirmation required:",
        !data.session,
      );

      return { error: null };
    } catch (error) {
      console.error("AuthProvider: Unexpected error during sign-up:", error);
      return {
        error: {
          message: "An unexpected error occurred during sign-up",
          status: 500,
        } as AuthError,
      };
    }
  };

  const signOut = async () => {
    console.log("AuthProvider: Signing out");
    try {
      await supabase.auth.signOut();
      console.log("AuthProvider: Sign-out successful");
    } catch (error) {
      console.error("AuthProvider: Error during sign-out:", error);
    }
  };

  const signInWithMagicLink = async (email: string) => {
    console.log("AuthProvider: Sending magic link to:", email);

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (error) {
        console.error(
          "AuthProvider: Magic link error:",
          error.message,
          error.status,
        );
        return { error };
      }

      console.log("AuthProvider: Magic link sent successfully");
      return { error: null };
    } catch (error) {
      console.error(
        "AuthProvider: Unexpected error sending magic link:",
        error,
      );
      return {
        error: {
          message: "An unexpected error occurred while sending the magic link",
          status: 500,
        } as AuthError,
      };
    }
  };

  const refreshSession = async (): Promise<boolean> => {
    console.log("AuthProvider: Attempting to refresh session");
    try {
      const { data, error } = await supabase.auth.refreshSession();

      if (error) {
        console.error("AuthProvider: Session refresh error:", error.message);
        return false;
      }

      if (!data.session) {
        console.log("AuthProvider: No session returned after refresh attempt");
        return false;
      }

      console.log("AuthProvider: Session refreshed successfully");
      console.log(
        "AuthProvider: New session expires at:",
        new Date(data.session.expires_at! * 1000).toISOString(),
      );
      return true;
    } catch (error) {
      console.error(
        "AuthProvider: Unexpected error refreshing session:",
        error,
      );
      return false;
    }
  };

  const value = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signOut,
    signInWithMagicLink,
    refreshSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
