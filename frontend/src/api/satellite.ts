import { apiClient } from './client';
import type { SatelliteResponse } from '../types/satellite';

/**
 * Fetch Sentinel-2 satellite indices for coordinates and temporal window
 * Endpoint: GET /api/satellite?latitude={lat}&longitude={lon}&start_date={start}&end_date={end}&radius_m={radius}
 */
export async function fetchSatellite(
  latitude: number,
  longitude: number,
  startDate: string,
  endDate: string,
  radiusM: number = 500
): Promise<SatelliteResponse> {
  const params = new URLSearchParams({
    latitude: latitude.toFixed(4),
    longitude: longitude.toFixed(4),
    start_date: startDate,
    end_date: endDate,
    radius_m: radiusM.toString(),
  });
  return apiClient<SatelliteResponse>(`/api/satellite?${params.toString()}`, {
    method: 'GET',
  });
}
