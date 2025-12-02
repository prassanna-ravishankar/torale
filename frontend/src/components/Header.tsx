import React from "react";
import { UserButton } from "@clerk/clerk-react";
import { Shield, Bell, BookOpen } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { Logo } from "@/components/Logo";

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
        <Link to="/dashboard" className="shrink-0">
          <Logo />
        </Link>

        {/* Navigation Links */}
        <div className="flex items-center gap-1 md:gap-2">
          {isAdmin && (
            <Link to="/admin">
              <Button
                variant={location.pathname === "/admin" ? "default" : "ghost"}
                size="sm"
                className="gap-1 md:gap-2 font-mono text-xs h-8 px-2 md:px-3"
              >
                <Shield className="h-4 w-4" />
                <span className="hidden sm:inline">Admin</span>
              </Button>
            </Link>
          )}

          {user && (
            <>
              <Link to="/settings/notifications">
                <Button
                  variant={location.pathname === "/settings/notifications" ? "default" : "ghost"}
                  size="sm"
                  className="gap-1 md:gap-2 font-mono text-xs h-8 px-2 md:px-3"
                >
                  <Bell className="h-4 w-4" />
                  <span className="hidden sm:inline">Settings</span>
                </Button>
              </Link>

              <a
                href="https://docs.torale.ai"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="ghost" size="sm" className="gap-1 md:gap-2 font-mono text-xs h-8 px-2 md:px-3">
                  <BookOpen className="h-4 w-4" />
                  <span className="hidden sm:inline">Docs</span>
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
