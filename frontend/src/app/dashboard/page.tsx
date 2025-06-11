"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export default function Dashboard() {
  const { user, session, loading, signOut } = useAuth();
  const [userName, setUserName] = useState<string>("");
  const [sessionStatus, setSessionStatus] = useState<string>("checking");

  // Check authentication on component mount
  useEffect(() => {
    async function setupDashboard() {
      try {
        console.log("[Dashboard] Component mounted, checking auth...");

        if (!session) {
          console.log("[Dashboard] No session found in context");
          setSessionStatus("no-session");
          return;
        }

        if (!user) {
          console.log("[Dashboard] Session exists but no user found");
          setSessionStatus("no-user");
          return;
        }

        // Log session details
        console.log("[Dashboard] Session details:", {
          user: user.email,
          expires_at: session.expires_at,
          has_access_token: !!session.access_token,
          has_refresh_token: !!session.refresh_token,
        });

        // Get user from session
        setUserName(user.email?.split("@")[0] || "User");
        setSessionStatus("authenticated");
        console.log("[Dashboard] User authenticated:", user.email);
      } catch (error) {
        console.error("[Dashboard] Unhandled error in dashboard setup:", error);
        setSessionStatus("error");
      }
    }

    if (!loading) {
      setupDashboard();
    }
  }, [user, session, loading]);

  const handleSignOut = async () => {
    await signOut();
    window.location.href = "/auth";
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-indigo-500 border-r-transparent"></div>
          <p className="mt-4 text-gray-700 text-lg">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user || !session) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-indigo-500 border-r-transparent"></div>
          <p className="mt-4 text-gray-700 text-lg">
            Redirecting to login... ({sessionStatus})
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-12">
          <div className="startup-card rounded-2xl p-8 text-center">
            <div className="mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4 animate-float">
                <span className="text-2xl font-bold text-white">
                  {userName.charAt(0).toUpperCase()}
                </span>
              </div>
              <h1 className="text-4xl font-bold gradient-text font-space-grotesk mb-2">
                Welcome back, {userName}!
              </h1>
              <p className="text-gray-600 text-lg">
                Your AI-powered monitoring dashboard is ready to keep you informed.
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <Link href="/discover" className="group">
            <div className="startup-card rounded-xl p-6 text-center group-hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                <span className="text-xl">🔍</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Discover Sources</h3>
              <p className="text-gray-600 text-sm">Find new content to monitor</p>
            </div>
          </Link>

          <Link href="/sources/new" className="group">
            <div className="startup-card rounded-xl p-6 text-center group-hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                <span className="text-xl">➕</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Add Source</h3>
              <p className="text-gray-600 text-sm">Monitor a specific URL</p>
            </div>
          </Link>

          <Link href="/alerts" className="group">
            <div className="startup-card rounded-xl p-6 text-center group-hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                <span className="text-xl">🔔</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">View Alerts</h3>
              <p className="text-gray-600 text-sm">Check recent changes</p>
            </div>
          </Link>

          <Link href="/profile" className="group">
            <div className="startup-card rounded-xl p-6 text-center group-hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
                <span className="text-xl">⚙️</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Settings</h3>
              <p className="text-gray-600 text-sm">Manage your account</p>
            </div>
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <DashboardCard
            title="Active Sources"
            count={0}
            icon={
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">📊</span>
              </div>
            }
            description="Currently monitoring"
            linkHref="/sources"
            gradient="from-blue-500 to-indigo-500"
          />

          <DashboardCard
            title="Recent Alerts"
            count={0}
            icon={
              <div className="w-8 h-8 bg-gradient-to-br from-red-500 to-pink-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">🔔</span>
              </div>
            }
            description="Changes detected today"
            linkHref="/alerts"
            gradient="from-red-500 to-pink-500"
          />

          <DashboardCard
            title="Discoveries"
            count={0}
            icon={
              <div className="w-8 h-8 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">🔍</span>
              </div>
            }
            description="Sources found this week"
            linkHref="/discover"
            gradient="from-emerald-500 to-teal-500"
          />

          <DashboardCard
            title="Uptime"
            count="99.9%"
            icon={
              <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">✅</span>
              </div>
            }
            description="System reliability"
            linkHref="/settings"
            gradient="from-green-500 to-emerald-500"
          />
        </div>

        {/* Recent Activity */}
        <div className="startup-card rounded-2xl p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
            <span className="mr-3">📈</span>
            Recent Activity
          </h2>
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📭</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No activity yet</h3>
            <p className="text-gray-500 mb-6">Start monitoring sources to see activity here</p>
            <Link
              href="/discover"
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-lg font-medium hover:from-indigo-600 hover:to-purple-600 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <span className="mr-2">🚀</span>
              Get Started
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

interface DashboardCardProps {
  title: string;
  count?: number | string;
  icon: React.ReactNode;
  description: string;
  linkHref: string;
  gradient: string;
}

function DashboardCard({
  title,
  count,
  icon,
  description,
  linkHref,
  gradient,
}: DashboardCardProps) {
  return (
    <Link href={linkHref} className="group">
      <div className="startup-card rounded-xl p-6 group-hover:scale-105 transition-all duration-300">
        <div className="flex items-center justify-between mb-4">
          {icon}
          {count !== undefined && (
            <div className={`text-2xl font-bold bg-gradient-to-r ${gradient} bg-clip-text text-transparent`}>
              {count}
            </div>
          )}
        </div>
        <h3 className="text-lg font-semibold text-gray-800 mb-1">{title}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </Link>
  );
}