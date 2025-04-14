"use client";

import React from "react";
import { useAuth } from "@/contexts/AuthContext";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { loading } = useAuth();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      {/* Show loading state or children */}
      {loading ? (
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-teal-500 border-r-transparent"></div>
          <p className="mt-2 text-gray-700">Loading...</p>
        </div>
      ) : (
        <>{children}</>
      )}
    </div>
  );
}
