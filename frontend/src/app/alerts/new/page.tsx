"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function NewAlertPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    query: "",
    target_url: "",
    target_type: "website",
    keywords: "",
    check_frequency_minutes: 30,
    similarity_threshold: 0.9,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // TODO: Implement API call
      console.log("Creating alert:", formData);
      router.push("/alerts");
    } catch (error) {
      console.error("Failed to create alert:", error);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Create New Alert</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label
            htmlFor="query"
            className="block text-sm font-medium text-gray-700"
          >
            Alert Query
          </label>
          <input
            type="text"
            id="query"
            value={formData.query}
            onChange={(e) =>
              setFormData({ ...formData, query: e.target.value })
            }
            placeholder="e.g., Tell me when OpenAI updates their research page"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div>
          <label
            htmlFor="target_url"
            className="block text-sm font-medium text-gray-700"
          >
            Target URL
          </label>
          <input
            type="url"
            id="target_url"
            value={formData.target_url}
            onChange={(e) =>
              setFormData({ ...formData, target_url: e.target.value })
            }
            placeholder="https://example.com"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div>
          <label
            htmlFor="target_type"
            className="block text-sm font-medium text-gray-700"
          >
            Target Type
          </label>
          <select
            id="target_type"
            value={formData.target_type}
            onChange={(e) =>
              setFormData({ ...formData, target_type: e.target.value })
            }
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="website">Website</option>
            <option value="rss">RSS Feed</option>
            <option value="youtube">YouTube Channel</option>
          </select>
        </div>

        <div>
          <label
            htmlFor="keywords"
            className="block text-sm font-medium text-gray-700"
          >
            Keywords (optional)
          </label>
          <input
            type="text"
            id="keywords"
            value={formData.keywords}
            onChange={(e) =>
              setFormData({ ...formData, keywords: e.target.value })
            }
            placeholder="e.g., GPT, model, research"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div>
          <label
            htmlFor="check_frequency"
            className="block text-sm font-medium text-gray-700"
          >
            Check Frequency (minutes)
          </label>
          <input
            type="number"
            id="check_frequency"
            value={formData.check_frequency_minutes}
            onChange={(e) =>
              setFormData({
                ...formData,
                check_frequency_minutes: parseInt(e.target.value),
              })
            }
            min="5"
            max="1440"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div>
          <label
            htmlFor="similarity_threshold"
            className="block text-sm font-medium text-gray-700"
          >
            Similarity Threshold (0-1)
          </label>
          <input
            type="number"
            id="similarity_threshold"
            value={formData.similarity_threshold}
            onChange={(e) =>
              setFormData({
                ...formData,
                similarity_threshold: parseFloat(e.target.value),
              })
            }
            min="0"
            max="1"
            step="0.1"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
          >
            Create Alert
          </button>
        </div>
      </form>
    </div>
  );
}
