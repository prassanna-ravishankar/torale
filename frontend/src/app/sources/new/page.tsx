'use client';

import React, { useEffect, Suspense } from 'react';
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 py-12">
      <div className="max-w-2xl mx-auto px-4">
        <button
          onClick={() => router.back()}
          className="mb-6 text-sm text-teal-600 hover:text-teal-800 flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Discover
        </button>

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mb-6 animate-float">
            <span className="text-2xl">➕</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold gradient-text font-space-grotesk mb-4">
            Add New Source
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Enter the URL you want to monitor and configure how often it should be checked for changes.
          </p>
        </div>

        {/* Main Form */}
        <div className="startup-card rounded-2xl p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label htmlFor="url" className="block text-lg font-semibold text-gray-800 mb-3">
                URL to Monitor <span className="text-red-500">*</span>
              </label>
              <input
                {...register('url')}
                type="url"
                id="url"
                className={`w-full px-4 py-4 text-lg border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 bg-white/80 backdrop-blur-sm ${errors.url ? 'border-red-500' : ''}`}
                placeholder="https://example.com/page-to-monitor"
                disabled={isSubmitting || createSourceMutation.isPending}
              />
              {errors.url && (
                <p className="mt-2 text-sm text-red-600">{errors.url.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="check_interval_seconds" className="block text-lg font-semibold text-gray-800 mb-3">
                Check Interval (seconds)
              </label>
              <input
                {...register('check_interval_seconds')}
                type="number"
                id="check_interval_seconds"
                className={`w-full px-4 py-4 text-lg border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 bg-white/80 backdrop-blur-sm ${errors.check_interval_seconds ? 'border-red-500' : ''}`}
                placeholder="3600"
                disabled={isSubmitting || createSourceMutation.isPending}
              />
              <p className="mt-2 text-sm text-gray-500">
                Minimum: 60 seconds. Default: 3600 seconds (1 hour). 
                <br />
                <strong>Common intervals:</strong> 300 (5 min), 1800 (30 min), 3600 (1 hour), 86400 (1 day)
              </p>
              {errors.check_interval_seconds && (
                <p className="mt-2 text-sm text-red-600">{errors.check_interval_seconds.message}</p>
              )}
            </div>

            <div className="pt-4">
              <button
                type="submit"
                disabled={isSubmitting || createSourceMutation.isPending}
                className="w-full py-4 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-lg font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-4 focus:ring-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none"
              >
                {(isSubmitting || createSourceMutation.isPending) ? (
                  <div className="flex items-center justify-center">
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Adding Source...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <span className="mr-2">🚀</span>
                    Add Monitored Source
                  </div>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Help Section */}
        <div className="startup-card rounded-2xl p-8 mt-8">
          <h3 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
            <span className="mr-3">💡</span>
            Tips for Better Monitoring
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-gray-700 mb-2">Choose the Right Interval</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• <strong>News sites:</strong> 5-15 minutes</li>
                  <li>• <strong>Blogs:</strong> 1-6 hours</li>
                  <li>• <strong>Product pages:</strong> 1-24 hours</li>
                  <li>• <strong>Documentation:</strong> 1-7 days</li>
                </ul>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-gray-700 mb-2">Best Practices</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Monitor specific pages, not homepages</li>
                  <li>• Use longer intervals for stable content</li>
                  <li>• Test with shorter intervals initially</li>
                  <li>• Respect website rate limits</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function CreateMonitoredSourcePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-indigo-500 border-r-transparent"></div>
          <p className="mt-4 text-gray-700 text-lg">Loading...</p>
        </div>
      </div>
    }>
      <CreateMonitoredSourcePageContent />
    </Suspense>
  );
}