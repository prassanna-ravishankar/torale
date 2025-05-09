'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import axiosInstance from '@/lib/axiosInstance';

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

const fetchMonitoredSources = async (): Promise<MonitoredSourceInDB[]> => {
  const response = await axiosInstance.get<MonitoredSourceInDB[]>('/monitored-sources/');
  return response.data;
};

export default function MonitoredSourcesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const {
    data: sources,
    isLoading,
    error,
    isError,
  } = useQuery<MonitoredSourceInDB[], Error>({
    queryKey: ['monitoredSources'],
    queryFn: fetchMonitoredSources,
  });

  // Mutation for deleting a source
  const deleteSourceMutation = useMutation<void, Error, number>({
    mutationFn: async (sourceId: number) => {
      await axiosInstance.delete(`/monitored-sources/${sourceId}`);
    },
    onSuccess: (_, sourceId) => {
      toast.success(`Source (ID: ${sourceId}) deleted successfully.`);
      queryClient.invalidateQueries({ queryKey: ['monitoredSources'] });
    },
    onError: (error, sourceId) => {
      toast.error(`Failed to delete source (ID: ${sourceId}). ${error.message}`);
      console.error("Error deleting source:", error);
    },
  });

  const handleDelete = (sourceId: number, sourceUrl: string) => {
    if (window.confirm(`Are you sure you want to delete the source: ${sourceUrl} (ID: ${sourceId})?`)) {
      deleteSourceMutation.mutate(sourceId);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-teal-500 border-r-transparent"></div>
        <p className="ml-4 text-gray-700 text-lg">Loading monitored sources...</p>
      </div>
    );
  }

  if (isError && error) {
    toast.error(error.message || 'Failed to load monitored sources.');
    return (
      <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8 text-center">
        <p className="text-red-600 text-lg">Error loading sources: {error.message}</p>
        <p className="text-gray-600 mt-2">Please try refreshing the page or contact support if the issue persists.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Monitored Sources</h1>
        <Link href="/sources/new"
          className="inline-flex items-center justify-center rounded-md border border-transparent bg-teal-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition duration-150 ease-in-out"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Add New Source
        </Link>
      </div>

      {sources && sources.length > 0 ? (
        <div className="bg-white shadow-md rounded-lg overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">URL</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Check Interval (s)</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Checked</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sources.map((source) => (
                <tr key={source.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 max-w-xs truncate" title={source.url}>{source.url}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{source.status}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{source.check_interval_seconds}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {source.last_checked_at ? new Date(source.last_checked_at).toLocaleString() : 'Never'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => router.push(`/sources/${source.id}/edit`)}
                      className="text-teal-600 hover:text-teal-900 transition duration-150 ease-in-out"
                      disabled={deleteSourceMutation.isPending && deleteSourceMutation.variables === source.id}
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(source.id, source.url)}
                      className="text-red-600 hover:text-red-900 transition duration-150 ease-in-out"
                      disabled={deleteSourceMutation.isPending && deleteSourceMutation.variables === source.id}
                    >
                      {(deleteSourceMutation.isPending && deleteSourceMutation.variables === source.id) ? 'Deleting...' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12">
          <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 17.25v-.228a4.5 4.5 0 00-.12-1.03l-2.268-9.64a3.375 3.375 0 00-3.285-2.602H7.923a3.375 3.375 0 00-3.285 2.602l-2.268 9.64a4.5 4.5 0 00-.12 1.03v.228m19.5 0a3 3 0 01-3 3H5.25a3 3 0 01-3-3m19.5 0a3 3 0 00-3-3H5.25a3 3 0 00-3 3m16.5 0h.008v.008h-.008v-.008zm-3 0h.008v.008h-.008v-.008z" />
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900">No Monitored Sources</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by adding a new source to monitor.</p>
          <div className="mt-6">
            <Link href="/sources/new"
              className="inline-flex items-center rounded-md border border-transparent bg-teal-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 transition duration-150 ease-in-out"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
              Add New Source
            </Link>
          </div>
        </div>
      )}
    </div>
  );
} 