import { apiClient } from './client';
import type { RecommendationRequest, RecommendationResponse } from '../types/recommendation';

/**
 * Request ML crop recommendations
 * Endpoint: POST /api/recommendations
 */
export async function fetchRecommendations(
  request: RecommendationRequest
): Promise<RecommendationResponse> {
  return apiClient<RecommendationResponse>('/api/recommendations', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
