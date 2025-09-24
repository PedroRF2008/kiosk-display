import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';

// Create a client with offline-friendly settings
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: (failureCount, error: any) => {
        // Don't retry on network errors, use cached data instead
        if (error?.message?.includes?.('NetworkError') || error?.message?.includes?.('Failed to fetch')) {
          return false;
        }
        return failureCount < 2;
      },
      staleTime: 5 * 60 * 1000, // 5 minutes - keep data fresh longer
      cacheTime: 30 * 60 * 1000, // 30 minutes - keep cached data longer for offline use
      refetchOnReconnect: true, // Refetch when connection is restored
      retryOnMount: false, // Don't retry on mount if data exists
    },
  },
});

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);