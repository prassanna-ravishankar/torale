'use client';

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
// If you want to use the React Query Devtools, uncomment the next line
// import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Create a new QueryClient instance. 
// We usually want to create this instance once and reuse it.
// For Next.js App Router, it's common to create it in a client component like this one.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Global default options for queries can go here, for example:
      // staleTime: 1000 * 60 * 5, // 5 minutes
      // refetchOnWindowFocus: false, // a common override
    },
  },
});

interface QueryProviderProps {
  children: React.ReactNode;
}

export default function QueryProvider({ children }: QueryProviderProps) {
  return (
    // Provide the client to your App
    <QueryClientProvider client={queryClient}>
      {children}
      {/* Optional: React Query Devtools for development - highly recommended */}
      {/* <ReactQueryDevtools initialIsOpen={false} /> */}
    </QueryClientProvider>
  );
} 