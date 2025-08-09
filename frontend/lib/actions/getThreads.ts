/**
 * Get threads list for timeline
 * Server-side helper function for fetching threads
 */

import { get, ApiError, NetworkError } from '@/lib/api';

// Thread type (simplified for list view)
export interface ThreadListItem {
  id: string;
  authorId: string;
  title: string;
  body: string;
  tags: Array<{ key: string; name: string }>;
  imageKey?: string;
  solvedCommentId?: string;
  upCount: number;
  saveCount: number;
  heat: number;
  isMine: boolean;
  createdAt: string;
  lastActivityAt: string;
  authorProfile?: {
    displayName: string;
    iconKind: string;
  };
  authorAffiliation?: {
    faculty: string;
    year: number;
  };
}

// Threads response with pagination
export interface ThreadsResponse {
  threads: ThreadListItem[];
  nextCursor?: string;
}

// Sort options
export type ThreadSort = 'new' | 'hot';

/**
 * Get threads list without authentication (public view)
 * @param sort Sort order (new or hot)
 * @param cursor Optional cursor for pagination
 * @returns Threads list with pagination info
 * @throws {ApiError} API error response
 * @throws {NetworkError} Network error
 */
export async function getThreads(
  sort: ThreadSort = 'new',
  cursor?: string
): Promise<ThreadsResponse> {
  try {
    // Build query parameters
    const params: Record<string, string> = { sort };
    if (cursor) {
      params.cursor = cursor;
    }

    // Call GET API without authentication
    const response = await get<ThreadsResponse>('/threads', { params });
    return response;
  } catch (error) {
    // Re-throw API and Network errors as-is
    if (error instanceof ApiError || error instanceof NetworkError) {
      throw error;
    }
    
    // Wrap other errors
    throw new Error('スレッド一覧の取得に失敗しました');
  }
}

/**
 * Get threads list with authentication (for is_mine flags)
 * @param sort Sort order (new or hot)
 * @param cursor Optional cursor for pagination
 * @param token Optional auth token
 * @returns Threads list with is_mine flags
 */
export async function getThreadsWithAuth(
  sort: ThreadSort = 'new',
  cursor?: string,
  token?: string
): Promise<ThreadsResponse> {
  try {
    // Build query parameters
    const params: Record<string, string> = { sort };
    if (cursor) {
      params.cursor = cursor;
    }

    // Call GET API with optional authentication
    const response = await get<ThreadsResponse>('/threads', { params, token });
    return response;
  } catch (error) {
    // Re-throw API and Network errors as-is
    if (error instanceof ApiError || error instanceof NetworkError) {
      throw error;
    }
    
    // Wrap other errors
    throw new Error('スレッド一覧の取得に失敗しました');
  }
}