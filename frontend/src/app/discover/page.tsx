'use client';

import React, { useState } from 'react';
import toast from 'react-hot-toast';
import axiosInstance from '@/lib/axiosInstance';
import axios from 'axios';
import { useRouter } from 'next/navigation';

interface MonitoredURLOutput {
  monitorable_urls: string[];
}

export default function DiscoverPage() {
  const router = useRouter();
  const [rawQuery, setRawQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [discoveredUrls, setDiscoveredUrls] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

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
    setDiscoveredUrls([]);

    try {
      const response = await axiosInstance.post<MonitoredURLOutput>(
        '/discover-sources/', 
        { raw_query: rawQuery }
      );
      if (response.data && response.data.monitorable_urls) {
        setDiscoveredUrls(response.data.monitorable_urls);
        if (response.data.monitorable_urls.length > 0) {
          toast.success(`Found ${response.data.monitorable_urls.length} potential sources!`);
        }
      } else {
        toast.error('Received an unexpected response from the server.');
      }
    } catch (err: unknown) {
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 py-12">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl mb-6 animate-float">
            <span className="text-2xl">🔍</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold gradient-text font-space-grotesk mb-4">
            Discover Sources
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Tell us what you want to monitor in natural language, and our AI will find the best sources for you.
          </p>
        </div>

        {/* Main Form */}
        <div className="startup-card rounded-2xl p-8 mb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="rawQuery" className="block text-lg font-semibold text-gray-800 mb-3">
                What would you like to monitor?
              </label>
              <div className="relative">
                <textarea
                  id="rawQuery"
                  name="rawQuery"
                  rows={4}
                  className="w-full px-4 py-4 text-lg border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all duration-300 resize-none bg-white/80 backdrop-blur-sm"
                  placeholder="e.g., 'Latest AI research from OpenAI', 'Tesla stock news and updates', 'New features on GitHub', 'Climate change policy updates'"
                  value={rawQuery}
                  onChange={(e) => setRawQuery(e.target.value)}
                  disabled={isLoading}
                />
                <div className="absolute bottom-3 right-3 text-sm text-gray-400">
                  {rawQuery.length}/500
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !rawQuery.trim()}
              className="w-full py-4 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-lg font-semibold rounded-xl hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-4 focus:ring-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Discovering Sources...
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <span className="mr-2">🚀</span>
                  Discover Sources
                </div>
              )}
            </button>
          </form>
        </div>

        {/* Error State */}
        {error && (
          <div className="startup-card rounded-xl p-6 mb-8 border-l-4 border-red-500">
            <div className="flex items-center">
              <span className="text-2xl mr-3">❌</span>
              <div>
                <h3 className="text-lg font-semibold text-red-800 mb-1">Discovery Failed</h3>
                <p className="text-red-600">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {discoveredUrls.length > 0 && (
          <div className="startup-card rounded-2xl p-8">
            <div className="flex items-center mb-6">
              <span className="text-2xl mr-3">✨</span>
              <h2 className="text-2xl font-bold text-gray-800">
                Found {discoveredUrls.length} Source{discoveredUrls.length !== 1 ? 's' : ''}
              </h2>
            </div>
            <div className="grid gap-4">
              {discoveredUrls.map((url, index) => (
                <div key={index} className="group bg-white/60 backdrop-blur-sm border border-gray-200 rounded-xl p-6 hover:border-indigo-300 hover:shadow-lg transition-all duration-300">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center mb-2">
                        <span className="text-lg mr-2">🌐</span>
                        <h3 className="text-lg font-semibold text-gray-800 truncate">
                          {url.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                        </h3>
                      </div>
                      <p className="text-gray-600 text-sm break-all">{url}</p>
                    </div>
                    <button
                      onClick={() => handleAddToMonitor(url)}
                      className="ml-4 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-medium rounded-lg hover:from-emerald-600 hover:to-teal-600 transition-all duration-300 shadow-md hover:shadow-lg transform hover:scale-105 flex items-center"
                    >
                      <span className="mr-2">➕</span>
                      Monitor This
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 text-center">
              <p className="text-gray-600 mb-4">Want to monitor all of these sources?</p>
              <button
                onClick={() => {
                  // Add all URLs to monitoring (you could implement batch add functionality)
                  toast.success('Batch monitoring feature coming soon!');
                }}
                className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-500 text-white font-medium rounded-lg hover:from-indigo-600 hover:to-purple-600 transition-all duration-300 shadow-md hover:shadow-lg transform hover:scale-105"
              >
                Monitor All Sources
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && discoveredUrls.length === 0 && rawQuery !== '' && !error && (
          <div className="startup-card rounded-2xl p-12 text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-2xl">🔍</span>
            </div>
            <h3 className="text-xl font-semibold text-gray-600 mb-3">No Sources Found</h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              We couldn&apos;t find any relevant sources for your query. Try rephrasing or being more specific.
            </p>
            <button
              onClick={() => {
                setRawQuery('');
                setError(null);
              }}
              className="px-6 py-3 bg-gradient-to-r from-gray-500 to-gray-600 text-white font-medium rounded-lg hover:from-gray-600 hover:to-gray-700 transition-all duration-300"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Examples */}
        {!rawQuery && (
          <div className="startup-card rounded-2xl p-8">
            <h3 className="text-xl font-semibold text-gray-800 mb-6 flex items-center">
              <span className="mr-3">💡</span>
              Try These Examples
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              {[
                "Latest AI research papers from top universities",
                "Tesla stock price and news updates",
                "New features and updates from GitHub",
                "Climate change policy announcements",
                "Cryptocurrency market analysis and trends",
                "Space exploration news from NASA and SpaceX"
              ].map((example, index) => (
                <button
                  key={index}
                  onClick={() => setRawQuery(example)}
                  className="text-left p-4 bg-white/60 backdrop-blur-sm border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all duration-300 group"
                >
                  <div className="flex items-center">
                    <span className="text-lg mr-3 group-hover:scale-110 transition-transform duration-300">💭</span>
                    <span className="text-gray-700 group-hover:text-indigo-600 transition-colors duration-300">
                      &ldquo;{example}&rdquo;
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}