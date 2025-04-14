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
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-teal-500 border-r-transparent"></div>
          <p className="mt-2 text-gray-700">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!user || !session) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-teal-500 border-r-transparent"></div>
          <p className="mt-2 text-gray-700">
            Redirecting to login... ({sessionStatus})
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 border-b pb-5">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome, {userName}!
        </h1>
        <p className="mt-2 text-gray-600">
          This is your Ambi Alert dashboard where you can monitor and manage
          your alerts.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <DashboardCard
          title="Active Alerts"
          count={0}
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
          }
          description="Monitor your current active alerts"
          linkHref="/alerts"
        />

        <DashboardCard
          title="Devices"
          count={0}
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8 text-blue-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
              />
            </svg>
          }
          description="Manage your connected devices"
          linkHref="/devices"
        />

        <DashboardCard
          title="Settings"
          icon={
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8 text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          }
          description="Configure your account and notifications"
          linkHref="/settings"
        />
      </div>

      <div className="mt-8 text-center">
        <button
          onClick={handleSignOut}
          className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded"
        >
          Sign Out
        </button>
      </div>
    </div>
  );
}

interface DashboardCardProps {
  title: string;
  count?: number;
  icon: React.ReactNode;
  description: string;
  linkHref: string;
}

function DashboardCard({
  title,
  count,
  icon,
  description,
  linkHref,
}: DashboardCardProps) {
  return (
    <Link href={linkHref} className="block">
      <div className="rounded-lg border bg-white p-6 shadow-sm transition duration-150 ease-in-out hover:shadow-md">
        <div className="flex items-center justify-between">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
            {icon}
          </div>
          {count !== undefined && (
            <div className="text-2xl font-bold text-gray-800">{count}</div>
          )}
        </div>
        <h3 className="mt-4 text-lg font-medium text-gray-900">{title}</h3>
        <p className="mt-2 text-sm text-gray-600">{description}</p>
      </div>
    </Link>
  );
}
