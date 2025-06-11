'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import toast from 'react-hot-toast';
import axiosInstance from '@/lib/axiosInstance';

// Zod schema for validation
const monitoredSourceCreateSchema = z.object({
  url: z.string().url({ message: "Invalid URL format." }).min(1, { message: "URL is required." }),
  check_interval_seconds: z.coerce
    .number()
    .int()
    .positive({ message: "Check interval must be a positive number." })
    .min(60, { message: "Check interval must be at least 60 seconds." })
    .optional(), // Making it optional as per API schema (MonitoredSourceCreate)
});

type MonitoredSourceCreateFormData = z.infer<typeof monitoredSourceCreateSchema>;

// Define the expected response structure from the backend (MonitoredSourceInDB)
interface MonitoredSourceInDB {
  id: number;
  url: string;
  check_interval_seconds: number;
  status: string;
  user_id: string; // Assuming user_id is part of the response
  created_at: string;
  updated_at: string;
  last_checked_at?: string | null;
  last_changed_at?: string | null;
}

function CreateMonitoredSourcePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const prefilledUrl = searchParams.get('url');
  const [formData, setFormData] = useState({
    query: "",
    target_url: "",
    target_type: "website",
    keywords: "",
    check_frequency_minutes: 30,
    similarity_threshold: 0.9,
  });

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<MonitoredSourceCreateFormData>({
    resolver: zodResolver(monitoredSourceCreateSchema),
    defaultValues: {
      url: prefilledUrl || '',
      check_interval_seconds: 3600, // Default to 1 hour, can be adjusted
    },
  });

  useEffect(() => {
    if (prefilledUrl) {
      setValue('url', prefilledUrl);
    }
  }, [prefilledUrl, setValue]);

  const createSourceMutation = useMutation<
    MonitoredSourceInDB, // Expected response type
    Error, // Error type
    MonitoredSourceCreateFormData // Input type to the mutation function
  >({
    mutationFn: async (data) => {
      const response = await axiosInstance.post<MonitoredSourceInDB>('/monitored-sources/', data);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Source added: ${data.url}`);
      queryClient.invalidateQueries({ queryKey: ['monitoredSources'] }); // Invalidate list query
      router.push('/sources'); // Redirect to the list page
    },
    onError: (error) => {
      // More specific error handling can be added here based on error content
      toast.error(error.message || 'Failed to add source. Please try again.');
      console.error("Error creating source:", error);
    },
  });

  const onSubmit = (data: MonitoredSourceCreateFormData) => {
    createSourceMutation.mutate(data);
  };

  const handleAlertSubmit = async (e: React.FormEvent) => {
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
    <div className="max-w-xl mx-auto p-4 sm:p-6 lg:p-8">
      <button
        onClick={() => router.back()}
        className="mb-6 text-sm text-teal-600 hover:text-teal-800 flex items-center"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Discover
      </button>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Add New Monitored Source</h1>
      <p className="text-gray-600 mb-6">
        Enter the URL you want to monitor and how often it should be checked.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 bg-white p-6 shadow-md rounded-lg">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
            URL to Monitor <span className="text-red-500">*</span>
          </label>
          <input
            {...register('url')}
            type="url"
            id="url"
            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 transition duration-150 ease-in-out sm:text-sm ${errors.url ? 'border-red-500' : ''}`}
            placeholder="https://example.com/article"
            disabled={isSubmitting || createSourceMutation.isPending}
          />
          {errors.url && (
            <p className="mt-1 text-sm text-red-600">{errors.url.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="check_interval_seconds" className="block text-sm font-medium text-gray-700 mb-1">
            Check Interval (seconds)
          </label>
          <input
            {...register('check_interval_seconds')}
            type="number"
            id="check_interval_seconds"
            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 transition duration-150 ease-in-out sm:text-sm ${errors.check_interval_seconds ? 'border-red-500' : ''}`}
            placeholder="e.g., 3600 for 1 hour, 86400 for 1 day"
            disabled={isSubmitting || createSourceMutation.isPending}
          />
          <p className="mt-1 text-xs text-gray-500">Minimum: 60 seconds. Default: 3600 seconds (1 hour).</p>
          {errors.check_interval_seconds && (
            <p className="mt-1 text-sm text-red-600">{errors.check_interval_seconds.message}</p>
          )}
        </div>

        <div>
          <button
            type="submit"
            disabled={isSubmitting || createSourceMutation.isPending}
            className="w-full inline-flex items-center justify-center rounded-md border border-transparent bg-teal-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition duration-150 ease-in-out"
          >
            {(isSubmitting || createSourceMutation.isPending) ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Adding Source...
              </>
            ) : (
              'Add Monitored Source'
            )}
          </button>
        </div>
      </form>

      <div className="mt-6">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">Create New Alert</h2>
        <p className="text-gray-600 mb-6">
          Enter the details for the new alert.
        </p>

        <form onSubmit={handleAlertSubmit} className="space-y-6">
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
    </div>
  );
}

export default function CreateMonitoredSourcePage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <CreateMonitoredSourcePageContent />
    </Suspense>
  );
} 