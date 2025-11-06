import React from "react";
import { UserButton } from "@clerk/clerk-react";
import { Bell } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export const Header: React.FC = () => {
  const { user } = useAuth();
  const noAuth = import.meta.env.VITE_TORALE_NOAUTH === '1';

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="h-6 w-6 text-primary" />
          <h2>Torale</h2>
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
