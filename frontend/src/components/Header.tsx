import React from "react";
import { UserButton, useUser } from "@clerk/clerk-react";
import { Bell } from "lucide-react";

export const Header: React.FC = () => {
  const { user } = useUser();

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
              {user.primaryEmailAddress?.emailAddress}
            </span>
          )}
          <UserButton afterSignOutUrl="/sign-in" />
        </div>
      </div>
    </header>
  );
};
