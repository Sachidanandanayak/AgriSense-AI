import { apiClient } from './client';

export interface HealthResponse {
  status: string;
}

export interface RootResponse {
  message: string;
}

export async function checkBackendHealth(): Promise<{ healthy: boolean; statusText: string }> {
  try {
    const res = await apiClient<HealthResponse>('/health', { method: 'GET' }, 5000);
    return {
      healthy: res.status === 'healthy',
      statusText: res.status || 'OK',
    };
  } catch (error) {
    return {
      healthy: false,
      statusText: error instanceof Error ? error.message : 'Offline',
    };
  }
}
