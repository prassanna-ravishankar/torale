"use client";

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import Image from 'next/image';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import axiosInstance from '@/lib/axiosInstance';

// Define the expected structure for a ChangeAlert (ChangeAlertSchema from backend)
interface ChangeAlertSchema {
  id: number;
  monitored_source_id: number;
  summary: string;
  details?: Record<string, unknown> | string | null; // Changed any to unknown
  screenshot_url?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  created_at: string;
  is_acknowledged: boolean;
  acknowledged_at?: string | null;
  // Potentially include source_url or name if backend provides it directly or via a join
  source_url?: string; // Example: to be fetched or joined by backend
}

interface FetchAlertsParams {
  skip?: number;
  limit?: number;
  monitored_source_id?: number;
  is_acknowledged?: boolean;
}

const fetchAlerts = async (params: FetchAlertsParams): Promise<ChangeAlertSchema[]> => {
  const response = await axiosInstance.get<ChangeAlertSchema[]>('/alerts/', { params });
  return response.data;
};

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  
  // Basic filtering state examples (can be expanded)
  const [filterAcknowledged, setFilterAcknowledged] = useState<boolean | undefined>(undefined);
  // TODO: Add state for monitored_source_id filter, skip, limit, sorting

  // Check authentication and redirect if not logged in
  useEffect(() => {
    if (!authLoading && !user) {
      toast.error('Please sign in to view alerts');
      router.push('/auth');
    }
  }, [user, authLoading, router]);

  const {
    data: alerts,
    isLoading,
    error,
    isError,
  } = useQuery<ChangeAlertSchema[], Error>({
    queryKey: ['alerts', { acknowledged: filterAcknowledged }], // Query key includes filters
    queryFn: () => fetchAlerts({ is_acknowledged: filterAcknowledged }),
    enabled: !!user, // Only run query if user is authenticated
    // keepPreviousData: true, // Useful for pagination/filtering to keep data while new is fetched
  });

  // Mutation for acknowledging an alert - Task 4.3
  const acknowledgeAlertMutation = useMutation<ChangeAlertSchema, Error, number>({
    mutationFn: async (alertId: number) => {
      const response = await axiosInstance.post<ChangeAlertSchema>(`/alerts/${alertId}/acknowledge`);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Alert (ID: ${data.id}) acknowledged.`);
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      // Optionally, update the specific alert in the cache if more granular control is needed
      // queryClient.setQueryData(['alerts', { id: data.id }], data);
    },
    onError: (error, alertId) => {
      toast.error(`Failed to acknowledge alert (ID: ${alertId}). ${error.message}`);
      console.error("Error acknowledging alert:", error);
    },
  });

  const handleAcknowledge = (alertId: number) => {
    acknowledgeAlertMutation.mutate(alertId);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-teal-500 border-r-transparent"></div>
        <p className="ml-4 text-gray-700 text-lg">Loading alerts...</p>
      </div>
    );
  }

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <div className="flex justify-center items-center min-h-[calc(100vh-200px)]">
        <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-teal-500 border-r-transparent"></div>
        <p className="ml-4 text-gray-700 text-lg">Checking authentication...</p>
      </div>
    );
  }

  // Don't render anything if not authenticated (redirect will happen)
  if (!user) {
    return null;
  }

  if (isError && error) {
    // Better error handling for authentication errors
    if (error.message.includes('403') || error.message.includes('Not authenticated')) {
      toast.error('Please sign in to view alerts');
      router.push('/auth');
      return null;
    }
    
    toast.error(error.message || 'Failed to load alerts.');
    return (
      <div className="max-w-4xl mx-auto p-4 sm:p-6 lg:p-8 text-center">
        <p className="text-red-600 text-lg">Error loading alerts: {error.message}</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6 lg:p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Change Alerts</h1>
        <Link href="/alerts/new" className="ml-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500">
          Define New Monitoring Task
        </Link>
        {/* Placeholder for global actions like "Acknowledge All" or bulk actions */}
      </div>

      {/* Placeholder for Filtering UI - Task 4.1 */}
      <div className="mb-6 p-4 bg-gray-100 rounded-lg">
        <h3 className="text-lg font-medium text-gray-800 mb-2">Filters (Placeholder)</h3>
        <div className="flex space-x-4 items-center">
          <div>
            <label htmlFor="filterAcknowledged" className="text-sm text-gray-600 mr-2">Status:</label>
            <select 
              id="filterAcknowledged"
              value={filterAcknowledged === undefined ? 'all' : filterAcknowledged ? 'acknowledged' : 'unacknowledged'}
              onChange={(e) => {
                const val = e.target.value;
                if (val === 'all') setFilterAcknowledged(undefined);
                else if (val === 'acknowledged') setFilterAcknowledged(true);
                else setFilterAcknowledged(false);
              }}
              className="rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm"
            >
              <option value="all">All</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="unacknowledged">Unacknowledged</option>
            </select>
          </div>
          {/* TODO: Add filter for monitored_source_id (e.g., dropdown populated from user's sources) */}
          {/* TODO: Add sorting options */}
        </div>
      </div>

      {alerts && alerts.length > 0 ? (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div key={alert.id} className={`bg-white shadow-md rounded-lg p-4 border-l-4 ${alert.is_acknowledged ? 'border-green-500' : 'border-red-500'}`}>
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">
                    <Link href={`/sources/${alert.monitored_source_id}`} className="hover:underline hover:text-teal-600">
                      Source ID: {alert.monitored_source_id} {alert.source_url ? `(${alert.source_url})` : ''}
                    </Link>
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">{alert.summary}</p>
                  <p className="text-xs text-gray-400 mt-1">Detected: {new Date(alert.created_at).toLocaleString()}</p>
                </div>
                {!alert.is_acknowledged && (
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    disabled={acknowledgeAlertMutation.isPending && acknowledgeAlertMutation.variables === alert.id}
                    className="ml-4 py-1 px-3 text-xs font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {acknowledgeAlertMutation.isPending && acknowledgeAlertMutation.variables === alert.id ? 'Ack...' : 'Acknowledge'}
                  </button>
                )}
              </div>
              {/* Placeholder for Detail View link/modal - Task 4.2 */}
              {/* Example: <Link href={`/alerts/${alert.id}`}>View Details</Link> */}
              {alert.details && <pre className="mt-2 p-2 bg-gray-50 text-xs text-gray-700 rounded overflow-x-auto">{typeof alert.details === 'string' ? alert.details : JSON.stringify(alert.details, null, 2)}</pre>}
              {alert.screenshot_url && (
                <div className="mt-2 relative w-full max-w-xs h-48 border border-gray-300 rounded overflow-hidden">
                  <Image 
                    src={alert.screenshot_url} 
                    alt="Change screenshot" 
                    fill 
                    style={{ objectFit: "contain" }}
                    className="rounded"
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <svg xmlns="http://www.w3.org/2000/svg" className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900">No Alerts Found</h3>
          <p className="mt-1 text-sm text-gray-500">There are currently no change alerts to display.</p>
          {filterAcknowledged !== undefined && <p className="mt-1 text-sm text-gray-500">Try adjusting your filters.</p>}
        </div>
      )}
    </div>
  );
}
