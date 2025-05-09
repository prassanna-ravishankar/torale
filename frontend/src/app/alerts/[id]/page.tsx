'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { /* useRouter, */ useParams } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import axiosInstance from '@/lib/axiosInstance';

// Reusing ChangeAlertSchema from the list page (ideally this would be in a shared types file)
interface ChangeAlertSchema {
  id: number;
  monitored_source_id: number;
  summary: string;
  details?: Record<string, unknown> | string | null;
  screenshot_url?: string | null;
  old_value?: string | null;
  new_value?: string | null;
  created_at: string;
  is_acknowledged: boolean;
  acknowledged_at?: string | null;
  source_url?: string; 
}

const fetchAlertById = async (id: string): Promise<ChangeAlertSchema> => {
  const response = await axiosInstance.get<ChangeAlertSchema>(`/alerts/${id}`);
  return response.data;
};

export default function AlertDetailPage() {
  // const router = useRouter(); // Removed unused router
  const params = useParams();
  const alertId = params.id as string;
  const queryClient = useQueryClient();

  const {
    data: alert,
    isLoading,
    isError,
    error,
  } = useQuery<ChangeAlertSchema, Error>({
    queryKey: ['alert', alertId],
    queryFn: () => fetchAlertById(alertId),
    enabled: !!alertId,
  });

  const acknowledgeAlertMutation = useMutation<ChangeAlertSchema, Error, number>({
    mutationFn: async (id: number) => {
      const response = await axiosInstance.post<ChangeAlertSchema>(`/alerts/${id}/acknowledge`);
      return response.data;
    },
    onSuccess: (data) => {
      toast.success(`Alert (ID: ${data.id}) acknowledged.`);
      queryClient.invalidateQueries({ queryKey: ['alerts'] }); // Invalidate list view
      queryClient.invalidateQueries({ queryKey: ['alert', data.id.toString()] }); // Invalidate this specific alert
      // queryClient.setQueryData(['alert', data.id.toString()], data); // Or update cache directly
    },
    onError: (err, id) => {
      toast.error(`Failed to acknowledge alert (ID: ${id}). ${err.message}`);
    },
  });

  const handleAcknowledge = () => {
    if (alert) {
      acknowledgeAlertMutation.mutate(alert.id);
    }
  };

  if (isLoading) {
    return <div className="text-center p-8">Loading alert details...</div>;
  }

  if (isError || !alert) {
    return <div className="text-center p-8 text-red-600">Error loading alert: {error?.message || 'Alert not found.'}</div>;
  }

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-6 lg:p-8">
      <Link href="/alerts"
        className="mb-6 inline-flex items-center text-sm text-teal-600 hover:text-teal-800"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Alerts List
      </Link>

      <div className="bg-white shadow-xl rounded-lg overflow-hidden">
        <div className={`p-6 border-b ${alert.is_acknowledged ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Alert Details (ID: {alert.id})</h1>
            {!alert.is_acknowledged && (
              <button
                onClick={handleAcknowledge}
                disabled={acknowledgeAlertMutation.isPending}
                className="py-2 px-4 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {acknowledgeAlertMutation.isPending ? 'Acknowledging...' : 'Acknowledge'}
              </button>
            )}
          </div>
          <p className={`mt-1 text-sm ${alert.is_acknowledged ? 'text-green-700' : 'text-red-700'}`}>
            Status: {alert.is_acknowledged ? `Acknowledged on ${alert.acknowledged_at ? new Date(alert.acknowledged_at).toLocaleString() : 'N/A'}` : 'Unacknowledged'}
          </p>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <h3 className="text-xs font-medium text-gray-500 uppercase">Monitored Source</h3>
            <p className="text-sm text-gray-900">
              <Link href={`/sources/${alert.monitored_source_id}`} className="text-teal-600 hover:underline">
                ID: {alert.monitored_source_id} {alert.source_url ? `(${alert.source_url})` : ''}
              </Link>
            </p>
          </div>
          <div>
            <h3 className="text-xs font-medium text-gray-500 uppercase">Detected On</h3>
            <p className="text-sm text-gray-900">{new Date(alert.created_at).toLocaleString()}</p>
          </div>
          <div>
            <h3 className="text-xs font-medium text-gray-500 uppercase">Summary</h3>
            <p className="text-sm text-gray-900 whitespace-pre-wrap">{alert.summary}</p>
          </div>

          {alert.details && (
            <div>
              <h3 className="text-xs font-medium text-gray-500 uppercase">Details</h3>
              <pre className="mt-1 p-3 bg-gray-100 text-sm text-gray-800 rounded-md overflow-x-auto whitespace-pre-wrap">
                {typeof alert.details === 'string' ? alert.details : JSON.stringify(alert.details, null, 2)}
              </pre>
            </div>
          )}

          {alert.old_value && (
            <div>
              <h3 className="text-xs font-medium text-gray-500 uppercase">Old Value</h3>
              <pre className="mt-1 p-3 bg-red-50 text-sm text-red-700 rounded-md overflow-x-auto whitespace-pre-wrap">{alert.old_value}</pre>
            </div>
          )}

          {alert.new_value && (
            <div>
              <h3 className="text-xs font-medium text-gray-500 uppercase">New Value</h3>
              <pre className="mt-1 p-3 bg-green-50 text-sm text-green-700 rounded-md overflow-x-auto whitespace-pre-wrap">{alert.new_value}</pre>
            </div>
          )}
          
          {alert.screenshot_url && (
            <div>
              <h3 className="text-xs font-medium text-gray-500 uppercase">Screenshot</h3>
              <img 
                src={alert.screenshot_url} 
                alt={`Screenshot for alert ${alert.id}`} 
                className="mt-1 rounded-md border border-gray-300 max-w-full h-auto object-contain"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 