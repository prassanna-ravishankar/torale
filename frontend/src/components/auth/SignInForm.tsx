import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import { AuthError } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabaseClient";
import { useAuth } from "@/contexts/AuthContext";

const signInSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type SignInFormData = z.infer<typeof signInSchema>;

export default function SignInForm() {
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

      // Use the auth context signIn method
      const { error, session } = await signIn(data.email, data.password);

      if (error) {
        // Check for specific error types
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

      // Session established successfully
      toast.success("Signed in successfully");

      // Verify session is immediately accessible by attempting to refresh
      console.log("[SignInForm] Verifying session with refresh");
      const refreshSuccessful = await refreshSession();
      console.log("[SignInForm] Session refresh result:", refreshSuccessful);

      // Delay redirect slightly to ensure logs are sent
      console.log("[SignInForm] About to redirect to dashboard");
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

      // Direct Supabase call for magic link
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (error) throw error;
      toast.success("Magic link sent! Check your email");
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
      toast.success("Confirmation email sent! Please check your inbox");
    } catch (error) {
      toast.error("Failed to send confirmation email");
      console.error("[SignInForm] Resend confirmation error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md space-y-6 bg-white p-8 rounded-xl shadow-lg">
      <div className="flex flex-col items-center">
        <div className="mb-4">
          <img
            src="/ambi-alert.png"
            alt="Ambi Alert Logo"
            className="h-24 w-24 object-contain"
          />
        </div>
        <h2 className="text-center text-2xl font-bold tracking-tight text-gray-900">
          Sign in to Ambi Alert
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Monitor and respond to alerts in real-time
        </p>
      </div>

      {emailNotConfirmed && (
        <div className="rounded-lg bg-amber-50 p-4 border border-amber-200">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-amber-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-amber-800">
                Email not confirmed
              </h3>
              <div className="mt-2 text-sm text-amber-700">
                <p>
                  Your email address hasn&apos;t been confirmed yet. Please
                  check your inbox for a confirmation email or click the button
                  below to resend it.
                </p>
                <div className="mt-4">
                  <button
                    type="button"
                    onClick={handleResendConfirmation}
                    disabled={isLoading}
                    className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-amber-700 bg-amber-100 hover:bg-amber-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition duration-150 ease-in-out"
                  >
                    Resend confirmation email
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email address
            </label>
            <div className="mt-1">
              <input
                {...register("email")}
                id="email"
                type="email"
                className="block w-full rounded-md border-gray-300 shadow-sm py-2 px-3 focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 transition duration-150 ease-in-out"
                placeholder="you@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.email.message}
                </p>
              )}
            </div>
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <div className="mt-1">
              <input
                {...register("password")}
                id="password"
                type="password"
                className="block w-full rounded-md border-gray-300 shadow-sm py-2 px-3 focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 transition duration-150 ease-in-out"
                placeholder="••••••"
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.password.message}
                </p>
              )}
            </div>
          </div>
        </div>

        <div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
              </>
            ) : (
              "Sign in"
            )}
          </button>
        </div>

        <div className="text-center">
          <button
            type="button"
            onClick={() => handleMagicLink(email)}
            className="text-sm font-medium text-teal-600 hover:text-teal-500 transition duration-150 ease-in-out"
            disabled={isLoading}
          >
            Sign in with magic link instead
          </button>
        </div>

        <div className="pt-2 text-center">
          <p className="text-sm text-gray-600">
            Don&apos;t have an account?{" "}
            <a
              href="/auth/signup"
              className="font-medium text-teal-600 hover:text-teal-500 transition duration-150 ease-in-out"
            >
              Sign up
            </a>
          </p>
        </div>
      </form>
    </div>
  );
}
