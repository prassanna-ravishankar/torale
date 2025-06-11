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
        "Account created successfully! Please check your email to verify your account.",
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
      <div className="w-full max-w-md space-y-6 bg-white p-8 rounded-xl shadow-lg">
        <div className="flex flex-col items-center">
          <div className="mb-4">
            <Image
              src="/ambi-alert.png"
              alt="Ambi Alert Logo"
              width={96}
              height={96}
              className="object-contain"
            />
          </div>
          <h2 className="text-center text-2xl font-bold tracking-tight text-gray-900">
            Verification Email Sent
          </h2>
        </div>

        <div className="rounded-lg bg-green-50 p-4 border border-green-200">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-green-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">
                Account created successfully
              </h3>
              <div className="mt-2 text-sm text-green-700">
                <p>
                  We&apos;ve sent a verification email to{" "}
                  <strong>{email}</strong>. Please check your inbox and follow
                  the instructions to verify your account.
                </p>
                <p className="mt-2">
                  If you don&apos;t see the email, please check your spam
                  folder.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="pt-4 text-center">
          <a
            href="/auth/signin"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition duration-150 ease-in-out"
          >
            Return to Sign In
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md space-y-6 bg-white p-8 rounded-xl shadow-lg">
      <div className="flex flex-col items-center">
        <div className="mb-4">
          <Image
            src="/ambi-alert.png"
            alt="Ambi Alert Logo"
            width={96}
            height={96}
            className="object-contain"
          />
        </div>
        <h2 className="text-center text-2xl font-bold tracking-tight text-gray-900">
          Create your account
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Get started with Ambi Alert
        </p>
      </div>

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

          <div>
            <label
              htmlFor="confirmPassword"
              className="block text-sm font-medium text-gray-700"
            >
              Confirm Password
            </label>
            <div className="mt-1">
              <input
                {...register("confirmPassword")}
                id="confirmPassword"
                type="password"
                className="block w-full rounded-md border-gray-300 shadow-sm py-2 px-3 focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 transition duration-150 ease-in-out"
                placeholder="••••••"
              />
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.confirmPassword.message}
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
                Creating account...
              </>
            ) : (
              "Sign up"
            )}
          </button>
        </div>

        <div className="pt-2 text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{" "}
            <a
              href="/auth/signin"
              className="font-medium text-teal-600 hover:text-teal-500 transition duration-150 ease-in-out"
            >
              Sign in
            </a>
          </p>
        </div>
      </form>
    </div>
  );
}
