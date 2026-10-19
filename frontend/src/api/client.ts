/**
 * Centralized API client for AgriSense AI backend communication.
 * Handles timeouts, network failure detection, and informative error formatting.
 */

const DEFAULT_TIMEOUT_MS = 25000;

export class ApiError extends Error {
  status?: number;
  data?: unknown;

  constructor(message: string, status?: number, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Get current configured API Base URL (supports runtime localStorage override for testing)
 */
export function getApiBaseUrl(): string {
  const localOverride = localStorage.getItem('agrisense_api_base_url');
  if (localOverride) {
    return localOverride.replace(/\/+$/, '');
  }
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  return (envUrl || 'http://127.0.0.1:8000').replace(/\/+$/, '');
}

/**
 * Set runtime API Base URL override
 */
export function setApiBaseUrl(url: string | null): void {
  if (url) {
    localStorage.setItem('agrisense_api_base_url', url.trim().replace(/\/+$/, ''));
  } else {
    localStorage.removeItem('agrisense_api_base_url');
  }
}

/**
 * Fetch wrapper with timeout and standardized error handling
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      let errorBody: unknown = null;
      try {
        errorBody = await response.json();
        if (errorBody && typeof errorBody === 'object' && 'detail' in errorBody) {
          const detail = (errorBody as { detail: unknown }).detail;
          errorMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
        }
      } catch {
        // Response was not JSON
      }
      throw new ApiError(errorMessage, response.status, errorBody);
    }

    return (await response.json()) as T;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(
        `Request to ${endpoint} timed out after ${timeoutMs / 1000}s. Please check backend connection.`,
        408
      );
    }
    const message = error instanceof Error ? error.message : 'Unknown network failure';
    throw new ApiError(
      `Cannot connect to AgriSense AI backend at ${baseUrl}. Ensure backend server is running (uvicorn app.main:app). Details: ${message}`
    );
  }
}
