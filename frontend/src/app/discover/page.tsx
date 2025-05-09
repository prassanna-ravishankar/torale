'use client';

import React, { useState } from 'react';
import toast from 'react-hot-toast';
import axiosInstance from '@/lib/axiosInstance'; // Our configured Axios instance
import axios from 'axios'; // Import axios to use AxiosError type
import { useRouter } from 'next/navigation'; // Import useRouter
// We'll need a schema for the form input if using react-hook-form and zod later
// For now, a simple state for the textarea will suffice for the initial setup.

// Define the expected response structure from the backend
interface MonitoredURLOutput {
  monitorable_urls: string[];
}

export default function DiscoverPage() {
  const router = useRouter(); // Initialize useRouter
  const [rawQuery, setRawQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [discoveredUrls, setDiscoveredUrls] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Updated function for Task 2.5
  const handleAddToMonitor = (url: string) => {
    router.push(`/sources/new?url=${encodeURIComponent(url)}`);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!rawQuery.trim()) {
      toast.error('Please enter a query.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setDiscoveredUrls([]); // Clear previous results

    try {
      const response = await axiosInstance.post<MonitoredURLOutput>(
        '/discover-sources/', 
        { raw_query: rawQuery }
      );
      if (response.data && response.data.monitorable_urls) {
        setDiscoveredUrls(response.data.monitorable_urls);
        if (response.data.monitorable_urls.length === 0) {
          // No specific toast needed, UI will show empty list or a message there.
          // toast('No URLs found for your query.'); // react-hot-toast default toast
        }
      } else {
        toast.error('Received an unexpected response from the server.');
      }
    } catch (err: unknown) { // Changed from any to unknown
      console.error("Error discovering sources:", err);
      let errorMessage = 'Failed to discover sources. Please try again.';
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4 sm:p-6 lg:p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">
        Discover New Sources
      </h1>
      <p className="text-gray-600 mb-6">
        Enter a topic, keyword, or a specific URL to find monitorable web sources.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="rawQuery" className="block text-sm font-medium text-gray-700">
            Your Query
          </label>
          <textarea
            id="rawQuery"
            name="rawQuery"
            rows={4}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-teal-500 focus:ring-teal-500 sm:text-sm transition duration-150 ease-in-out"
            placeholder="e.g., 'latest advancements in AI', 'example.com/blog', 'Tesla stock news'"
            value={rawQuery}
            onChange={(e) => setRawQuery(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div>
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-teal-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition duration-150 ease-in-out w-full sm:w-auto"
          >
            {isLoading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Discovering...
              </>
            ) : (
              'Discover Sources'
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-6 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md">
          <p>{error}</p>
        </div>
      )}

      {discoveredUrls.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Discovered URLs</h2>
          <ul className="space-y-2">
            {discoveredUrls.map((url, index) => (
              <li key={index} className="p-3 bg-white shadow rounded-md text-sm text-gray-700 flex justify-between items-center">
                <span>{url}</span>
                <button
                  onClick={() => handleAddToMonitor(url)}
                  className="ml-4 py-1 px-3 text-xs font-medium text-white bg-green-600 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 transition duration-150 ease-in-out"
                >
                  Add to Monitor
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!isLoading && discoveredUrls.length === 0 && rawQuery !== '' && !error && (
        <div className="mt-6 p-3 bg-blue-100 border border-blue-400 text-blue-700 rounded-md">
          <p>No URLs found for your query. Try a different search term.</p>
        </div>
      )}
    </div>
  );
} 