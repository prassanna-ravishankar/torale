import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/contexts/AuthContext";
import toast from "react-hot-toast";
import { AuthError } from "@supabase/supabase-js";
import Image from 'next/image';

const signUpSchema = z
  .object({
    email: z.string().email("Invalid email address"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

type SignUpFormData = z.infer<typeof signUpSchema>;

interface SignUpFormProps {
  onSuccess?: () => void;
}

export default function SignUpForm({ onSuccess }: SignUpFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [signupSuccess, setSignupSuccess] = useState(false);
  const { signUp } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<SignUpFormData>({
    resolver: zodResolver(signUpSchema),
  });

  const email = watch("email");

  const onSubmit = async (data: SignUpFormData) => {
    try {
      setIsLoading(true);
      console.log("[SignUpForm] Creating account for:", data.email);

      const { error } = await signUp(data.email, data.password);

      if (error) {
        console.error("[SignUpForm] Signup error:", error.message);

        if (error.message.includes("User already registered")) {
          toast.error(
            "This email is already registered. Please sign in instead.",
          );
          return;
        }

        throw error;
      }

      console.log("[SignUpForm] Account created successfully");
      setSignupSuccess(true);
      toast.success(
        "Account created! 🎉 Please check your email to verify your account.",
      );
    } catch (error) {
      const authError = error as AuthError;
      if (authError.message) {
        toast.error(authError.message);
      } else {
        toast.error("Failed to create account");
      }
      console.error("[SignUpForm] Sign up error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (signupSuccess) {
    return (
      <div className="w-full space-y-6 text-center">
        <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-float">
          <span className="text-2xl">✅</span>
        </div>
        <h2 className="text-2xl font-bold gradient-text font-space-grotesk">
          Check Your Email
        </h2>
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-4 border border-emerald-200">
          <div className="flex items-start">
            <span className="text-xl mr-3 mt-1">📧</span>
            <div className="text-left">
              <h3 className="text-sm font-semibold text-emerald-800 mb-2">
                Verification email sent!
              </h3>
              <p className="text-emerald-700 mb-3 text-sm">
                We&apos;ve sent a verification email to{" "}
                <strong className="font-semibold">{email}</strong>
              </p>
              <p className="text-emerald-600 text-xs">
                Please check your inbox and follow the instructions to verify your account.
                Don&apos;t forget to check your spam folder!
              </p>
            </div>
          </div>
        </div>
        <div className="mt-6">
          <button
            onClick={() => onSuccess?.()}
            className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-semibold rounded-xl hover:from-indigo-600 hover:to-purple-600 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            Return to Sign In
          </button>
        </div>
      </div>
    );
  }

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
          Join Torale
        </h2>
        <p className="mt-2 text-gray-600">
          Start monitoring what matters to you
        </p>
      </div>

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

        <div>
          <label
            htmlFor="confirmPassword"
            className="block text-sm font-semibold text-gray-700 mb-2"
          >
            Confirm Password
          </label>
          <input
            {...register("confirmPassword")}
            id="confirmPassword"
            type="password"
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 bg-white"
            placeholder="••••••••"
          />
          {errors.confirmPassword && (
            <p className="mt-2 text-sm text-red-600">
              {errors.confirmPassword.message}
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
              Creating account...
            </div>
          ) : (
            <div className="flex items-center justify-center">
              <span className="mr-2">🚀</span>
              Create Account
            </div>
          )}
        </button>
      </form>
    </div>
  );
}