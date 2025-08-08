/**
 * API Client for Kyudai Campus SNS
 */

// API configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';

// Error types
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: any[],
    public requestId?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string, public cause?: Error) {
    super(message);
    this.name = 'NetworkError';
  }
}

// Error response type (matches backend ErrorResponse)
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any[];
    requestId?: string;
  };
}

// Request options
export interface RequestOptions extends RequestInit {
  token?: string;
  params?: Record<string, string | number | boolean>;
  timeout?: number;
}

/**
 * Parse error response from API
 */
async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const data = await response.json() as ErrorResponse;
    return new ApiError(
      response.status,
      data.error.code,
      data.error.message,
      data.error.details,
      data.error.requestId
    );
  } catch {
    // If response is not JSON, return generic error
    return new ApiError(
      response.status,
      'UNKNOWN_ERROR',
      `HTTP ${response.status}: ${response.statusText}`
    );
  }
}

/**
 * Build URL with query parameters
 */
function buildUrl(path: string, params?: Record<string, string | number | boolean>): string {
  const url = new URL(path, API_BASE_URL);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  
  return url.toString();
}

/**
 * Base fetch wrapper with common configuration
 */
async function fetchWithConfig(
  path: string,
  options: RequestOptions = {}
): Promise<Response> {
  const { token, params, timeout = 30000, ...fetchOptions } = options;
  
  // Build URL with query parameters
  const url = buildUrl(path, params);
  
  // Prepare headers
  const headers = new Headers(fetchOptions.headers);
  
  // Set default content type if not specified
  if (!headers.has('Content-Type') && fetchOptions.body && typeof fetchOptions.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }
  
  // Add authorization token if provided
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    // Check for HTTP errors
    if (!response.ok) {
      throw await parseErrorResponse(response);
    }
    
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    
    // Handle network errors
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new NetworkError('Request timeout', error);
      }
      if (error instanceof ApiError) {
        throw error;
      }
      throw new NetworkError('Network request failed', error);
    }
    
    throw error;
  }
}

/**
 * GET request
 */
export async function get<T = any>(
  path: string,
  options?: RequestOptions
): Promise<T> {
  const response = await fetchWithConfig(path, {
    ...options,
    method: 'GET',
  });
  
  if (response.status === 204) {
    return null as T;
  }
  
  return response.json();
}

/**
 * POST request
 */
export async function post<T = any>(
  path: string,
  body?: any,
  options?: RequestOptions
): Promise<T> {
  const response = await fetchWithConfig(path, {
    ...options,
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
  
  if (response.status === 204) {
    return null as T;
  }
  
  return response.json();
}

/**
 * PATCH request
 */
export async function patch<T = any>(
  path: string,
  body?: any,
  options?: RequestOptions
): Promise<T> {
  const response = await fetchWithConfig(path, {
    ...options,
    method: 'PATCH',
    body: body ? JSON.stringify(body) : undefined,
  });
  
  if (response.status === 204) {
    return null as T;
  }
  
  return response.json();
}

/**
 * DELETE request
 */
export async function del<T = any>(
  path: string,
  options?: RequestOptions
): Promise<T> {
  const response = await fetchWithConfig(path, {
    ...options,
    method: 'DELETE',
  });
  
  if (response.status === 204) {
    return null as T;
  }
  
  return response.json();
}

/**
 * PUT request (for file uploads)
 */
export async function put<T = any>(
  path: string,
  body?: any,
  options?: RequestOptions
): Promise<T> {
  const response = await fetchWithConfig(path, {
    ...options,
    method: 'PUT',
    body: body instanceof FormData || body instanceof Blob ? body : JSON.stringify(body),
  });
  
  if (response.status === 204) {
    return null as T;
  }
  
  return response.json();
}

// Export client object with all methods
const apiClient = {
  get,
  post,
  patch,
  delete: del,
  put,
  ApiError,
  NetworkError,
};

export default apiClient;