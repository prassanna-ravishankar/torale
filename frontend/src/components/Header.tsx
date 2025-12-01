import React from "react";
import { UserButton } from "@clerk/clerk-react";
import { Shield, Bell, BookOpen } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

/**
 * Header - Brutalist navigation for authenticated app
 * Mobile-first responsive design
 */

export const Header: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const noAuth = import.meta.env.VITE_TORALE_NOAUTH === '1';
  const isAdmin = user?.publicMetadata?.role === "admin";

  return (
    <header className="border-b-2 border-zinc-200 bg-white sticky top-0 z-40">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-2 shrink-0">
          <div className="bg-zinc-900 text-white w-8 h-8 flex items-center justify-center font-grotesk font-bold text-lg hover:bg-[hsl(10,90%,55%)] transition-colors">
            τ
          </div>
          <span className="font-grotesk font-bold text-xl tracking-tight hidden sm:inline">torale</span>
        </Link>

        {/* Navigation Links - Hidden on mobile */}
        <div className="hidden md:flex items-center gap-2">
          {isAdmin && (
            <Link to="/admin">
              <Button
                variant={location.pathname === "/admin" ? "default" : "ghost"}
                size="sm"
                className="gap-2 font-mono text-xs"
              >
                <Shield className="h-4 w-4" />
                Admin
              </Button>
            </Link>
          )}

          {user && (
            <>
              <Link to="/settings/notifications">
                <Button
                  variant={location.pathname === "/settings/notifications" ? "default" : "ghost"}
                  size="sm"
                  className="gap-2 font-mono text-xs"
                >
                  <Bell className="h-4 w-4" />
                  Settings
                </Button>
              </Link>

              <a
                href="https://docs.torale.ai"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="ghost" size="sm" className="gap-2 font-mono text-xs">
                  <BookOpen className="h-4 w-4" />
                  Docs
                </Button>
              </a>
            </>
          )}
        </div>

        {/* User Menu */}
        <div className="flex items-center gap-3 shrink-0">
          {user && (
            <span className="text-xs text-zinc-400 font-mono hidden lg:inline truncate max-w-[200px]">
              {user.email}
              {noAuth && " (Dev)"}
            </span>
          )}
          {!noAuth && <UserButton afterSignOutUrl="/sign-in" />}
        </div>
      </div>
    </header>
  );
};
