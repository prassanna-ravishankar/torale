"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import toast from 'react-hot-toast';
// import axiosInstance from '@/lib/axiosInstance'; // Commented out as API call is placeholder
import { isAxiosError } from 'axios';

// Commented out as payload structure will be for a new endpoint
// interface MonitoringTaskPayload {
//   url: string;
//   name?: string | null;
//   check_interval_seconds?: number;
//   source_type?: string | null;
//   keywords?: string[] | null;
//   config?: Record<string, unknown> | null;
// }

export default function NewMonitoringTaskPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    query: "",
    target_type: "website",
    keywords: "",
    check_frequency_minutes: 30,
    similarity_threshold: 0.9,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    if (!formData.query.trim()) {
      toast.error("Monitoring Task Name / Query Description is required.");
      setIsSubmitting(false);
      return;
    }

    const payload = {
      query_text: formData.query,
      config_hints: {
        source_type: formData.target_type || null,
        keywords: formData.keywords ? formData.keywords.split(',').map(k => k.trim()).filter(k => k) : null,
        check_interval_seconds: formData.check_frequency_minutes * 60,
        similarity_threshold: formData.similarity_threshold,
      }
    };

    try {
      console.log("Submitting new monitoring task query:", payload);
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.success(`Monitoring task initiated for: "${formData.query}"`);
    } catch (error: unknown) {
      console.error("Failed to initiate monitoring task:", error);
      let errorMessage = "Failed to initiate task. Please try again.";
      if (isAxiosError(error)) {
        errorMessage = error.response?.data?.detail || error.message || errorMessage;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto p-4 sm:p-6 lg:p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Define New Monitoring Task</h1>

      <form onSubmit={handleSubmit} className="space-y-6 bg-white p-6 shadow-md rounded-lg">
        <div>
          <label
            htmlFor="query"
            className="block text-sm font-medium text-gray-700"
          >
            Monitoring Task Name / Query Description <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="query"
            value={formData.query}
            onChange={(e) =>
              setFormData({ ...formData, query: e.target.value })
            }
            placeholder="e.g., Latest developments in AI safety research"
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm"
            disabled={isSubmitting}
          />
          <p className="mt-1 text-xs text-gray-500">Describe what you want to monitor. The system will try to discover relevant sources.</p>
        </div>

        <div>
          <label
            htmlFor="target_type"
            className="block text-sm font-medium text-gray-700"
          >
            Source Type
          </label>
          <select
            id="target_type"
            value={formData.target_type}
            onChange={(e) =>
              setFormData({ ...formData, target_type: e.target.value })
            }
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm"
            disabled={isSubmitting}
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
            Keywords (comma-separated, optional)
          </label>
          <input
            type="text"
            id="keywords"
            value={formData.keywords}
            onChange={(e) =>
              setFormData({ ...formData, keywords: e.target.value })
            }
            placeholder="e.g., GPT, model, research"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm"
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label
            htmlFor="check_frequency_minutes"
            className="block text-sm font-medium text-gray-700"
          >
            Check Frequency (minutes)
          </label>
          <input
            type="number"
            id="check_frequency_minutes"
            value={formData.check_frequency_minutes}
            onChange={(e) =>
              setFormData({
                ...formData,
                check_frequency_minutes: parseInt(e.target.value) > 0 ? parseInt(e.target.value) : 1,
              })
            }
            min="1"
            max="10080"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm"
            disabled={isSubmitting}
          />
        </div>

        <div>
          <label
            htmlFor="similarity_threshold"
            className="block text-sm font-medium text-gray-700"
          >
            Similarity Threshold (0.0 - 1.0, optional)
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
            min="0.0"
            max="1.0"
            step="0.01"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm"
            disabled={isSubmitting}
          />
          <p className="mt-1 text-xs text-gray-500">Advanced: Controls sensitivity to changes for some source types.</p>
        </div>

        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={() => router.back()}
            disabled={isSubmitting}
            className="rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-teal-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 disabled:opacity-50"
          >
            {isSubmitting ? 'Creating...' : 'Start Monitoring Task'}
          </button>
        </div>
      </form>
    </div>
  );
}
