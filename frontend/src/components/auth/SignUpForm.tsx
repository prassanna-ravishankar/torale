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

export default function SignUpForm() {
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
      <div className="w-full max-w-md space-y-8">
        <div className="startup-card rounded-2xl p-8 text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-6 animate-float">
            <span className="text-3xl">✅</span>
          </div>
          <h2 className="text-3xl font-bold gradient-text font-space-grotesk mb-4">
            Check Your Email
          </h2>
          <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-6 border border-emerald-200">
            <div className="flex items-start">
              <span className="text-2xl mr-3 mt-1">📧</span>
              <div className="text-left">
                <h3 className="text-lg font-semibold text-emerald-800 mb-2">
                  Verification email sent!
                </h3>
                <p className="text-emerald-700 mb-3">
                  We&apos;ve sent a verification email to{" "}
                  <strong className="font-semibold">{email}</strong>
                </p>
                <p className="text-emerald-600 text-sm">
                  Please check your inbox and follow the instructions to verify your account.
                  Don&apos;t forget to check your spam folder!
                </p>
              </div>
            </div>
          </div>
          <div className="mt-8">
            <button
              onClick={() => window.location.href = '/auth'}
              className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-semibold rounded-xl hover:from-indigo-600 hover:to-purple-600 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              Return to Sign In
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md space-y-8">
      <div className="startup-card rounded-2xl p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center mb-6 animate-float">
            <Image
              src="/ambi-alert.png"
              alt="Ambi Alert Logo"
              width={40}
              height={40}
              className="object-contain"
            />
          </div>
          <h2 className="text-3xl font-bold gradient-text font-space-grotesk text-center">
            Join AmbiAlert
          </h2>
          <p className="mt-3 text-center text-gray-600 text-lg">
            Start monitoring what matters to you
          </p>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
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
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 bg-white/80 backdrop-blur-sm"
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
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 bg-white/80 backdrop-blur-sm"
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
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 bg-white/80 backdrop-blur-sm"
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

      <div className="text-center">
        <p className="text-gray-600">
          Already have an account?{" "}
          <button
            onClick={() => window.location.href = '/auth'}
            className="font-semibold text-indigo-600 hover:text-indigo-500 transition-colors duration-300"
          >
            Sign in here
          </button>
        </p>
      </div>
    </div>
  );
}