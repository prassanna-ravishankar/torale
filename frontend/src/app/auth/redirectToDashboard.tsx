"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function RedirectToDashboard() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) {
      console.log("[RedirectToDashboard] Still loading auth state, waiting...");
      return;
    }

    if (user) {
      console.log(
        "[RedirectToDashboard] User authenticated, redirecting to dashboard...",
      );
      console.log("[RedirectToDashboard] User email:", user.email);

      // Try multiple redirection methods for reliable redirect
      try {
        router.push("/dashboard");

        // Fallback: direct navigation after a short delay
        setTimeout(() => {
          console.log("[RedirectToDashboard] Fallback redirect activated");
          window.location.href = "/dashboard";
        }, 500);
      } catch (e) {
        console.error("[RedirectToDashboard] Router redirect error:", e);
        // Last resort - direct navigation
        window.location.href = "/dashboard";
      }
    } else {
      console.log("[RedirectToDashboard] No authenticated user found");
    }
  }, [user, loading, router]);

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="mb-4">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-teal-500 border-r-transparent"></div>
        </div>
        <p className="text-lg text-gray-700">
          {loading ? "Checking authentication..." : "Redirecting..."}
        </p>
      </div>
    </div>
  );
}
