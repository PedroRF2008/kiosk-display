import {
  DisplayData,
  WeatherResponse,
  BirthdayResponse,
  MediaResponse,
  NewsResponse,
  SettingsResponse,
} from '../types';

const API_BASE_URL = process.env.NODE_ENV === 'development'
  ? 'http://localhost:5000/api/v1'
  : '/api/v1';

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      credentials: 'include', // Include cookies for session auth
      ...options,
    });

    if (!response.ok) {
      throw new ApiError(`HTTP error! status: ${response.status}`, response.status);
    }

    const data = await response.json();

    if (data.error) {
      throw new ApiError(data.error);
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// Display data APIs
export const displayApi = {
  getDisplayData: (): Promise<DisplayData> => fetchApi('/display'),
  getWeather: (): Promise<WeatherResponse> => fetchApi('/weather'),
  getBirthdays: (): Promise<BirthdayResponse> => fetchApi('/birthdays'),
  getMedia: (): Promise<MediaResponse> => fetchApi('/media'),
};

// Admin APIs
export const adminApi = {
  getNews: (): Promise<NewsResponse> => fetchApi('/admin/news'),
  getSettings: (): Promise<SettingsResponse> => fetchApi('/admin/settings'),

  // Add more admin endpoints as needed
  updateSettings: (settings: any): Promise<any> =>
    fetchApi('/admin/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),
};

// Auth APIs
export const authApi = {
  login: (password: string): Promise<any> =>
    fetchApi('/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `password=${encodeURIComponent(password)}`,
    }),

  logout: (): Promise<any> => fetchApi('/logout'),
};

export { ApiError };