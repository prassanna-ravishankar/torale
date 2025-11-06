import React from "react";
import { UserButton } from "@clerk/clerk-react";
import { Bell, Shield } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

export const Header: React.FC = () => {
  const { user } = useAuth();
  const location = useLocation();
  const noAuth = import.meta.env.VITE_TORALE_NOAUTH === '1';
  const isAdmin = user?.publicMetadata?.role === "admin";

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2">
            <Bell className="h-6 w-6 text-primary" />
            <h2>Torale</h2>
          </Link>

          {isAdmin && (
            <Link to="/admin">
              <Button
                variant={location.pathname === "/admin" ? "default" : "ghost"}
                size="sm"
                className="gap-2"
              >
                <Shield className="h-4 w-4" />
                Admin
              </Button>
            </Link>
          )}
        </div>

        <div className="flex items-center gap-4">
          {user && (
            <span className="text-sm text-muted-foreground hidden sm:inline">
              {user.email}
              {noAuth && " (Dev Mode)"}
            </span>
          )}
          {!noAuth && <UserButton afterSignOutUrl="/sign-in" />}
        </div>
      </div>
    </header>
  );
};
