import { useQuery } from '@tanstack/react-query';
import { displayApi } from '../utils/api';
import type { DisplayData, WeatherData, Birthday, MediaItem } from '../types';

// Main display data hook with offline support
export const useDisplayData = () => {
  return useQuery<DisplayData>({
    queryKey: ['displayData'],
    queryFn: displayApi.getDisplayData,
    refetchInterval: (_, query) => {
      // If there's an error (network issue), increase interval to reduce spam
      if (query.state.error) {
        return 60000; // 1 minute when there's an error
      }
      return 30000; // 30 seconds when working normally
    },
    retry: (failureCount, error: any) => {
      // Don't retry network errors immediately, rely on refetch interval
      if (error?.message?.includes?.('NetworkError') || error?.message?.includes?.('Failed to fetch')) {
        return false;
      }
      return failureCount < 2;
    },
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    // Don't show loading state when refetching with cached data
    notifyOnChangeProps: ['data', 'error'],
  });
};

// Individual data hooks for more granular control
export const useWeatherData = () => {
  return useQuery<WeatherData | null>({
    queryKey: ['weather'],
    queryFn: async () => {
      const response = await displayApi.getWeather();
      return response.weather;
    },
    refetchInterval: 300000, // Refetch every 5 minutes
    retry: 2,
  });
};

export const useBirthdayData = () => {
  return useQuery<Birthday[]>({
    queryKey: ['birthdays'],
    queryFn: async () => {
      const response = await displayApi.getBirthdays();
      return response.birthdays;
    },
    refetchInterval: 3600000, // Refetch every hour
    retry: 2,
  });
};

export const useMediaData = () => {
  return useQuery<MediaItem[]>({
    queryKey: ['media'],
    queryFn: async () => {
      const response = await displayApi.getMedia();
      return response.media;
    },
    refetchInterval: 60000, // Refetch every minute
    retry: 2,
  });
};