import { apiClient } from './client';
import type { SoilResponse } from '../types/soil';

/**
 * Fetch ISRIC SoilGrids 2.0 properties for coordinates
 * Endpoint: GET /api/soil?latitude={lat}&longitude={lon}&depth={depth}
 */
export async function fetchSoil(
  latitude: number,
  longitude: number,
  depth: string = '0-5cm'
): Promise<SoilResponse> {
  const params = new URLSearchParams({
    latitude: latitude.toFixed(4),
    longitude: longitude.toFixed(4),
    depth: depth,
  });
  return apiClient<SoilResponse>(`/api/soil?${params.toString()}`, {
    method: 'GET',
  });
}
