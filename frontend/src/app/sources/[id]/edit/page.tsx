'use client';

import React, { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter, useParams } from 'next/navigation';
import toast from 'react-hot-toast';
import axiosInstance from '@/lib/axiosInstance';

// Zod schema for MonitoredSourceUpdate (all fields optional)
const monitoredSourceUpdateSchema = z.object({
  url: z.string().url({ message: "Invalid URL format." }).min(1, { message: "URL cannot be empty." }).optional(),
  check_interval_seconds: z.coerce
    .number()
    .int()
    .positive({ message: "Check interval must be a positive number." })
    .min(60, { message: "Check interval must be at least 60 seconds." })
    .optional(),
  status: z.enum(['active', 'paused', 'error']).optional(), // Assuming these are possible statuses
});

type MonitoredSourceUpdateFormData = z.infer<typeof monitoredSourceUpdateSchema>;

// Define the expected structure for a MonitoredSource (MonitoredSourceInDB from backend)
interface MonitoredSourceInDB {
  id: number;
  url: string;
  check_interval_seconds: number;
  status: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  last_checked_at?: string | null;
  last_changed_at?: string | null;
}

const fetchMonitoredSourceById = async (id: string): Promise<MonitoredSourceInDB> => {
  const response = await axiosInstance.get<MonitoredSourceInDB>(`/monitored-sources/${id}`);
  return response.data;
};

export default function EditMonitoredSourcePage() {
  const router = useRouter();
  const params = useParams();
  const sourceId = params.id as string; // Will be a string from the URL
  const queryClient = useQueryClient();

  const {
    data: sourceData,
    isLoading: isLoadingSource,
    isError: isErrorSource,
    error: sourceError,
  } = useQuery<MonitoredSourceInDB, Error>({
    queryKey: ['monitoredSource', sourceId],
    queryFn: () => fetchMonitoredSourceById(sourceId),
    enabled: !!sourceId, // Only run query if sourceId is available
  });

  const {
    register,
    handleSubmit,
    reset, // To set form values once data is loaded
    formState: { errors, isSubmitting },
  } = useForm<MonitoredSourceUpdateFormData>({
    resolver: zodResolver(monitoredSourceUpdateSchema),
  });

  // Populate form with fetched data
  useEffect(() => {
    if (sourceData) {
      reset({
        url: sourceData.url,
        check_interval_seconds: sourceData.check_interval_seconds,
        status: sourceData.status as 'active' | 'paused' | 'error', // Cast to ensure compatibility
      });
    }
  }, [sourceData, reset]);

  const updateSourceMutation = useMutation<
    MonitoredSourceInDB,
    Error,
    MonitoredSourceUpdateFormData
  >({
    mutationFn: async (data) => {
      const response = await axiosInstance.put<MonitoredSourceInDB>(`/monitored-sources/${sourceId}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Source updated: ${data.url}`);
      queryClient.invalidateQueries({ queryKey: ['monitoredSources'] }); // Invalidate the list view
      queryClient.invalidateQueries({ queryKey: ['monitoredSource', sourceId] }); // Invalidate this specific source
      router.push('/sources');
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update source. Please try again.');
      console.error("Error updating source:", error);
    },
  });

  const onSubmit = (data: MonitoredSourceUpdateFormData) => {
    // Filter out undefined values before submitting, as API might not expect nulls for unchanged optionals
    const payload: MonitoredSourceUpdateFormData = {};
    if (data.url !== undefined) payload.url = data.url;
    if (data.check_interval_seconds !== undefined) payload.check_interval_seconds = data.check_interval_seconds;
    if (data.status !== undefined) payload.status = data.status;
    
    updateSourceMutation.mutate(payload);
  };

  if (isLoadingSource) {
    return <div className="text-center p-8">Loading source details...</div>;
  }

  if (isErrorSource || !sourceData) {
    return <div className="text-center p-8 text-red-600">Error loading source: {sourceError?.message || 'Source not found.'}</div>;
  }

  return (
    <div className="max-w-xl mx-auto p-4 sm:p-6 lg:p-8">
      <button
        onClick={() => router.push('/sources')}
        className="mb-6 text-sm text-teal-600 hover:text-teal-800 flex items-center"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Sources
      </button>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Edit Monitored Source</h1>
      <p className="text-gray-600 mb-6">Modify the details for <code className='bg-gray-100 px-1 rounded'>{sourceData.url}</code>.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 bg-white p-6 shadow-md rounded-lg">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-1">
            URL to Monitor
          </label>
          <input
            {...register('url')}
            type="url"
            id="url"
            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 sm:text-sm ${errors.url ? 'border-red-500' : ''}`}
            disabled={isSubmitting || updateSourceMutation.isPending}
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
            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 sm:text-sm ${errors.check_interval_seconds ? 'border-red-500' : ''}`}
            disabled={isSubmitting || updateSourceMutation.isPending}
          />
          <p className="mt-1 text-xs text-gray-500">Minimum: 60 seconds.</p>
          {errors.check_interval_seconds && (
            <p className="mt-1 text-sm text-red-600">{errors.check_interval_seconds.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            {...register('status')}
            id="status"
            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring focus:ring-teal-500 focus:ring-opacity-50 sm:text-sm ${errors.status ? 'border-red-500' : ''}`}
            disabled={isSubmitting || updateSourceMutation.isPending}
          >
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="error">Error (will attempt to re-activate)</option> 
          </select>
          {errors.status && (
            <p className="mt-1 text-sm text-red-600">{errors.status.message}</p>
          )}
        </div>

        <div>
          <button
            type="submit"
            disabled={isSubmitting || updateSourceMutation.isPending}
            className="w-full inline-flex items-center justify-center rounded-md border border-transparent bg-teal-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {(isSubmitting || updateSourceMutation.isPending) ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Saving Changes...
              </>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </form>
    </div>
  );
} 