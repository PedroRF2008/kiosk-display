// Weather data types
export interface WeatherData {
  city: string;
  weather: string;
  icon: string;
  temperature: number;
  temp_min: number;
  temp_max: number;
  rain_chance: number;
  humidity: number;
}

// Birthday data types
export interface Birthday {
  name: string;
  sector: string;
  date: string;
  is_today: boolean;
}

// Media data types
export interface MediaItem {
  id: string;
  type: string;
  url: string;
  local_path: string;
  duration: number;
  is_video: boolean;
  width: number;
  height: number;
  title?: string;
  description?: string;
}

// Device types
export type DeviceType = 'display_tv' | 'vertical_tv';

// Device info types
export interface DeviceInfo {
  type: DeviceType;
  name: string;
  description: string;
  id: string;
}

// Display data response
export interface DisplayData {
  weather: WeatherData | null;
  media: MediaItem[];
  birthdays: Birthday[];
  device: DeviceInfo | null;
  version: string;
  configured: boolean;
  error?: string;
}

// Admin data types
export interface NewsItem {
  id: number;
  title: string;
  content: string;
  media_path: string | null;
  duration: number;
  created_at: string;
}

export interface AdminSettings {
  weather: {
    apiKey: string;
    location: string;
  };
}

// API response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export interface WeatherResponse {
  weather: WeatherData | null;
}

export interface BirthdayResponse {
  birthdays: Birthday[];
}

export interface MediaResponse {
  media: MediaItem[];
  error?: string;
}

export interface NewsResponse {
  news: NewsItem[];
  error?: string;
}

export interface SettingsResponse {
  weather: {
    apiKey: string;
    location: string;
  };
  error?: string;
}