import { apiClient } from './client';
import type { WeatherResponse } from '../types/weather';

/**
 * Fetch normalized weather observations for coordinates
 * Endpoint: GET /api/weather?latitude={lat}&longitude={lon}
 */
export async function fetchWeather(latitude: number, longitude: number): Promise<WeatherResponse> {
  const params = new URLSearchParams({
    latitude: latitude.toFixed(4),
    longitude: longitude.toFixed(4),
  });
  return apiClient<WeatherResponse>(`/api/weather?${params.toString()}`, {
    method: 'GET',
  });
}
