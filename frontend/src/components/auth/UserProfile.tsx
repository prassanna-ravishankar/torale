import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/lib/supabaseClient";
import toast from "react-hot-toast";
import type { SupabaseClient } from "@supabase/supabase-js";

const profileSchema = z.object({
  full_name: z
    .string()
    .min(2, "Full name must be at least 2 characters")
    .nullable(),
  avatar_url: z.string().url("Invalid URL").nullable().optional(),
  website: z
    .string()
    .url("Invalid URL")
    .nullable()
    .optional()
    .or(z.literal("")),
});

type ProfileFormData = z.infer<typeof profileSchema>;

interface ProfileData {
  full_name: string | null;
  avatar_url?: string | null;
  website?: string | null;
}

export default function UserProfile() {
  const { user, loading: authLoading } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);

  const typedSupabase = supabase as SupabaseClient;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: "",
      avatar_url: "",
      website: "",
    },
  });

  useEffect(() => {
    if (user) {
      console.log("[UserProfile] User found, fetching profile...");
      setIsFetching(true);
      typedSupabase
        .from("profiles")
        .select("*")
        .eq("id", user.id)
        .single<ProfileData>()
        .then(({ data, error }) => {
          if (error && error.code !== "PGRST116") {
            console.error("[UserProfile] Error fetching profile:", error);
            toast.error("Failed to load profile data.");
          } else if (data) {
            console.log("[UserProfile] Profile data fetched:", data);
            reset({
              full_name: data.full_name,
              avatar_url: data.avatar_url,
              website: data.website,
            });
          } else {
            console.log(
              "[UserProfile] No profile data found for user:",
              user.id,
            );
            reset({ full_name: "", avatar_url: "", website: "" });
          }
          setIsFetching(false);
        });
    } else if (!authLoading) {
      console.log("[UserProfile] No user logged in.");
      setIsFetching(false);
    }
  }, [user, reset, authLoading, typedSupabase]);

  const onSubmit = async (data: ProfileFormData) => {
    if (!user) return;

    try {
      setIsLoading(true);
      console.log("[UserProfile] Updating profile with data:", data);

      const { error } = await typedSupabase
        .from("profiles")
        .update({
          full_name: data.full_name,
          avatar_url: data.avatar_url,
          website: data.website,
          updated_at: new Date().toISOString(),
        })
        .eq("id", user.id)
        .select()
        .single();

      if (error) throw error;
      toast.success("Profile updated successfully");
      console.log("[UserProfile] Profile update successful.");
    } catch (error) {
      toast.error("Failed to update profile");
      console.error("[UserProfile] Profile update error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading || isFetching) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-teal-500 border-r-transparent"></div>
        <p className="ml-3 text-gray-700">Loading profile...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="text-center text-red-600 p-8">
        Please log in to view your profile.
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4 bg-white shadow-md rounded-lg">
      <h2 className="text-2xl font-semibold mb-6 text-gray-800">
        Profile Settings
      </h2>
      <p className="mb-4 text-sm text-gray-600">
        Update your personal information.
      </p>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <label
            htmlFor="full_name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Full Name
          </label>
          <input
            {...register("full_name")}
            type="text"
            id="full_name"
            placeholder="Your full name"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 transition duration-150 ease-in-out sm:text-sm"
          />
          {errors.full_name && (
            <p className="mt-1 text-sm text-red-600">
              {errors.full_name.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="avatar_url"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Avatar URL
          </label>
          <input
            {...register("avatar_url")}
            type="url"
            id="avatar_url"
            placeholder="https://example.com/avatar.png"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 transition duration-150 ease-in-out sm:text-sm"
          />
          {errors.avatar_url && (
            <p className="mt-1 text-sm text-red-600">
              {errors.avatar_url.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="website"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Website
          </label>
          <input
            {...register("website")}
            type="url"
            id="website"
            placeholder="https://yourwebsite.com"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 transition duration-150 ease-in-out sm:text-sm"
          />
          {errors.website && (
            <p className="mt-1 text-sm text-red-600">
              {errors.website.message}
            </p>
          )}
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={isLoading || isFetching}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-teal-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition duration-150 ease-in-out"
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
                Saving...
              </>
            ) : (
              "Save Changes"
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
