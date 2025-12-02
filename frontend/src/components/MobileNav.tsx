import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Bell, Shield } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

/**
 * MobileNav - Bottom navigation bar for mobile screens
 * Only shown on md breakpoint and below
 */

export const MobileNav: React.FC = () => {
  const location = useLocation();
  const { user } = useAuth();
  const isAdmin = user?.publicMetadata?.role === 'admin';

  // Don't show mobile nav on landing, auth, or changelog pages
  const hiddenPaths = ['/', '/sign-in', '/sign-up', '/waitlist', '/changelog'];
  if (hiddenPaths.some(path => location.pathname.startsWith(path))) {
    return null;
  }

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Home' },
    { path: '/settings/notifications', icon: Bell, label: 'Settings' },
  ];

  if (isAdmin) {
    navItems.push({ path: '/admin', icon: Shield, label: 'Admin' });
  }

  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return location.pathname === '/dashboard';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-zinc-200 safe-area-inset-bottom">
      <div className="flex items-center justify-around h-16">
        {navItems.map(({ path, icon: Icon, label }) => {
          const active = isActive(path);
          return (
            <Link
              key={path}
              to={path}
              className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                active
                  ? 'text-zinc-900 bg-zinc-50'
                  : 'text-zinc-400 hover:text-zinc-600 active:bg-zinc-50'
              }`}
            >
              <Icon className="h-5 w-5 mb-1" />
              <span className="text-[10px] font-mono uppercase tracking-wider">
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};
