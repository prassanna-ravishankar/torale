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
        setIsSignIn(true);
      } else if (errorDescription) {
        errorMessage = errorDescription;
      } else {
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full opacity-10 animate-float"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-br from-blue-400 to-indigo-400 rounded-full opacity-10 animate-float" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="relative z-10 w-full max-w-md">
        {/* Toggle Buttons */}
        <div className="flex mb-8 bg-white/80 backdrop-blur-sm rounded-xl p-1 border border-gray-200">
          <button
            onClick={() => setIsSignIn(true)}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
              isSignIn
                ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg"
                : "text-gray-600 hover:text-gray-800"
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => setIsSignIn(false)}
            className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-300 ${
              !isSignIn
                ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg"
                : "text-gray-600 hover:text-gray-800"
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Forms */}
        <div className="transition-all duration-500 ease-in-out">
          {isSignIn ? <SignInForm /> : <SignUpForm />}
        </div>
      </div>
    </div>
  );
}