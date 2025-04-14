"use client";

import UserProfile from "@/components/auth/UserProfile";

export default function ProfilePage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <UserProfile />
      </div>
    </div>
  );
}
