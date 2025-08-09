/**
 * Get thread details
 * Server-side helper function for fetching thread details
 */

import { get, ApiError, NetworkError } from '@/lib/api';

// Thread type definition
export interface Thread {
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

// Thread ID validation regex
const THREAD_ID_REGEX = /^thr_[0-9A-HJKMNP-TV-Z]{26}$/;

/**
 * Validate thread ID format
 */
function validateThreadId(threadId: string): void {
  const trimmedId = threadId.trim();
  
  if (!trimmedId) {
    throw new Error('スレッドIDが必要です');
  }
  
  if (!THREAD_ID_REGEX.test(trimmedId)) {
    throw new Error('無効なスレッドIDです');
  }
}

/**
 * Get thread details without authentication (public view)
 * @param threadId The ID of the thread to fetch
 * @returns Thread details
 * @throws {Error} Validation error
 * @throws {ApiError} API error response (404, etc.)
 * @throws {NetworkError} Network error
 */
export async function getThread(threadId: string): Promise<Thread> {
  // Trim and validate thread ID
  const trimmedId = threadId.trim();
  validateThreadId(trimmedId);

  try {
    // Call GET API without authentication
    const thread = await get<Thread>(`/threads/${trimmedId}`);
    return thread;
  } catch (error) {
    // Re-throw API and Network errors as-is
    if (error instanceof ApiError || error instanceof NetworkError) {
      throw error;
    }
    
    // Wrap other errors
    throw new Error('スレッドの取得に失敗しました');
  }
}

/**
 * Get thread details with authentication (for is_mine flag)
 * @param threadId The ID of the thread to fetch
 * @param token Optional auth token
 * @returns Thread details with is_mine flag
 */
export async function getThreadWithAuth(threadId: string, token?: string): Promise<Thread> {
  // Trim and validate thread ID
  const trimmedId = threadId.trim();
  validateThreadId(trimmedId);

  try {
    // Call GET API with optional authentication
    const thread = await get<Thread>(`/threads/${trimmedId}`, { token });
    return thread;
  } catch (error) {
    // Re-throw API and Network errors as-is
    if (error instanceof ApiError || error instanceof NetworkError) {
      throw error;
    }
    
    // Wrap other errors
    throw new Error('スレッドの取得に失敗しました');
  }
}