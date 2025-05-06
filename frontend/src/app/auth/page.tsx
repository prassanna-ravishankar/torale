"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import SignInForm from "@/components/auth/SignInForm";
import SignUpForm from "@/components/auth/SignUpForm";
import toast from "react-hot-toast";
import { supabase } from "@/lib/supabaseClient";

export default function AuthPage() {
  const [isSignIn, setIsSignIn] = useState(true);
  const searchParams = useSearchParams();

  // Handle error parameters from URL (typically from auth callback)
  useEffect(() => {
    const error = searchParams.get("error");
    const errorDescription = searchParams.get("error_description");

    if (error) {
      console.log("[AuthPage] Error parameter detected:", error);

      // Map common error messages to user-friendly versions
      let errorMessage = "Authentication error";
      let shouldClearCookies = false;

      if (error === "no_code_found") {
        errorMessage =
          "Authentication code missing. Please try signing in again.";
      } else if (error === "no_session_returned") {
        errorMessage = "Unable to establish a session. Please try again.";
      } else if (error === "server_error") {
        errorMessage =
          "Server error during authentication. Please try again later.";
      } else if (error === "session_error") {
        errorMessage =
          "Your session is invalid or expired. Please sign in again.";
        shouldClearCookies = true;
      } else if (error.includes("Invalid login")) {
        errorMessage = "Invalid email or password.";
      } else if (error.includes("Email not confirmed")) {
        errorMessage = "Please confirm your email before signing in.";
        // Switch to sign in form if on sign up when this error occurs
        setIsSignIn(true);
      } else if (errorDescription) {
        // Use the error description if available
        errorMessage = errorDescription;
      } else {
        // Use the raw error message as fallback
        errorMessage = error;
      }

      toast.error(errorMessage);
      console.log("[AuthPage] Displayed error toast:", errorMessage);

      // Clear auth cookies if needed
      if (shouldClearCookies) {
        console.log("[AuthPage] Clearing auth cookies due to session error");
        supabase.auth
          .signOut()
          .then(() => {
            console.log("[AuthPage] Auth state cleared");
          })
          .catch((err: Error) => {
            console.error("[AuthPage] Error clearing auth state:", err);
          });
      }
    }

    // Check for return_to parameter and log it for debugging
    const returnTo = searchParams.get("return_to");
    if (returnTo) {
      console.log("[AuthPage] Return-to path detected:", returnTo);
    }
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        {isSignIn ? <SignInForm /> : <SignUpForm />}

        <div className="text-center">
          <button
            type="button"
            onClick={() => {
              console.log(
                "[AuthPage] Switching to",
                isSignIn ? "sign up" : "sign in",
                "form",
              );
              setIsSignIn(!isSignIn);
            }}
            className="text-sm font-medium text-teal-600 hover:text-teal-500"
          >
            {isSignIn
              ? "Don't have an account? Sign up"
              : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}
