import { apiClient } from './client';
import type { FarmAdvisoryRequest, FarmAdvisoryResponse } from '../types/advisory';

/**
 * Request evidence-based farm advisory report grounded in FAO ECOCROP & FAO-56
 * Endpoint: POST /api/advisory
 */
export async function fetchFarmAdvisory(
  request: FarmAdvisoryRequest
): Promise<FarmAdvisoryResponse> {
  return apiClient<FarmAdvisoryResponse>('/api/advisory', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
