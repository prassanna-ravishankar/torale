import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import { AuthError } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabaseClient";
import { useAuth } from "@/contexts/AuthContext";
import Image from 'next/image';

const signInSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type SignInFormData = z.infer<typeof signInSchema>;

interface SignInFormProps {
  onSuccess?: () => void;
}

export default function SignInForm({ onSuccess }: SignInFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [emailNotConfirmed, setEmailNotConfirmed] = useState(false);
  const { signIn, refreshSession } = useAuth();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
  });

  const email = watch("email");

  const onSubmit = async (data: SignInFormData) => {
    try {
      setIsLoading(true);
      setEmailNotConfirmed(false);
      console.log("[SignInForm] Signing in with:", data.email);

      const { error, session } = await signIn(data.email, data.password);

      if (error) {
        console.log(
          "[SignInForm] Auth error details:",
          error.message,
          error.status,
        );

        if (error.message.includes("Email not confirmed")) {
          setEmailNotConfirmed(true);
          toast.error("Please confirm your email before signing in");
          return;
        }

        if (error.message.includes("Invalid login")) {
          toast.error("Invalid email or password");
          return;
        }

        throw error;
      }

      if (!session) {
        console.error(
          "[SignInForm] No session returned after successful sign-in",
        );
        toast.error("Session could not be established");
        return;
      }

      toast.success("Welcome back! 🎉");

      const refreshSuccessful = await refreshSession();
      console.log("[SignInForm] Session refresh result:", refreshSuccessful);

      console.log("[SignInForm] About to redirect to dashboard");
      onSuccess?.();
      setTimeout(() => {
        console.log("[SignInForm] Performing redirect now");
        window.location.href = "/dashboard";
      }, 200);
    } catch (error) {
      const authError = error as AuthError;
      if (authError.message) {
        toast.error(authError.message);
        console.error("[SignInForm] Auth error:", authError.message);
        console.error("[SignInForm] Auth error details:", authError);
      } else {
        toast.error("Failed to sign in");
        console.error("[SignInForm] Unknown sign in error:", error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleMagicLink = async (email: string) => {
    if (!email) {
      toast.error("Please enter your email address");
      return;
    }

    if (!z.string().email().safeParse(email).success) {
      toast.error("Please enter a valid email address");
      return;
    }

    try {
      setIsLoading(true);
      setEmailNotConfirmed(false);

      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (error) throw error;
      toast.success("Magic link sent! ✨ Check your email");
    } catch (error) {
      const authError = error as AuthError;
      if (authError.message) {
        toast.error(authError.message);
      } else {
        toast.error("Failed to send magic link");
      }
      console.error("[SignInForm] Magic link error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendConfirmation = async () => {
    if (!email) {
      toast.error("Please enter your email address");
      return;
    }

    try {
      setIsLoading(true);
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (error) throw error;
      toast.success("Confirmation email sent! 📧 Please check your inbox");
    } catch (error) {
      toast.error("Failed to send confirmation email");
      console.error("[SignInForm] Resend confirmation error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full space-y-6">
      <div className="text-center mb-6">
        <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-float">
          <Image
            src="/torale-logo.svg"
            alt="Torale Logo"
            width={32}
            height={32}
            className="object-contain"
          />
        </div>
        <h2 className="text-2xl font-bold gradient-text font-space-grotesk">
          Welcome Back
        </h2>
        <p className="mt-2 text-gray-600">
          Sign in to your Torale account
        </p>
      </div>

      {emailNotConfirmed && (
        <div className="rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 p-4 border border-amber-200 mb-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-xl">⚠️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-semibold text-amber-800">
                Email not confirmed
              </h3>
              <div className="mt-2 text-amber-700 text-sm">
                <p className="mb-3">
                  Your email address hasn&apos;t been confirmed yet. Please
                  check your inbox for a confirmation email.
                </p>
                <button
                  type="button"
                  onClick={handleResendConfirmation}
                  disabled={isLoading}
                  className="px-3 py-1 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg text-sm font-medium hover:from-amber-600 hover:to-orange-600 transition-all duration-300 disabled:opacity-50"
                >
                  Resend confirmation email
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-semibold text-gray-700 mb-2"
          >
            Email address
          </label>
          <input
            {...register("email")}
            id="email"
            type="email"
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 bg-white"
            placeholder="you@example.com"
          />
          {errors.email && (
            <p className="mt-2 text-sm text-red-600">
              {errors.email.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-semibold text-gray-700 mb-2"
          >
            Password
          </label>
          <input
            {...register("password")}
            id="password"
            type="password"
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 bg-white"
            placeholder="••••••••"
          />
          {errors.password && (
            <p className="mt-2 text-sm text-red-600">
              {errors.password.message}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-lg font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-4 focus:ring-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none"
        >
          {isLoading ? (
            <div className="flex items-center justify-center">
              <svg
                className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Signing in...
            </div>
          ) : (
            <div className="flex items-center justify-center">
              <span className="mr-2">🚀</span>
              Sign In
            </div>
          )}
        </button>

        <div className="text-center">
          <button
            type="button"
            onClick={() => handleMagicLink(email)}
            className="text-indigo-600 hover:text-indigo-500 font-medium transition-colors duration-300 text-sm"
            disabled={isLoading}
          >
            ✨ Sign in with magic link instead
          </button>
        </div>
      </form>
    </div>
  );
}