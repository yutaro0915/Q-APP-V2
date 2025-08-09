/**
 * Delete thread action
 * Client-side helper function for deleting threads
 */

import { del, ApiError, NetworkError } from '@/lib/api';

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
 * Delete a thread
 * @param threadId The ID of the thread to delete
 * @returns Success result object
 * @throws {Error} Validation error
 * @throws {ApiError} API error response (401, 403, 404, etc.)
 * @throws {NetworkError} Network error
 */
export async function deleteThread(threadId: string): Promise<{ success: boolean }> {
  // Get auth token from localStorage
  const token = localStorage.getItem('auth_token');
  if (!token) {
    throw new Error('認証が必要です');
  }

  // Trim and validate thread ID
  const trimmedId = threadId.trim();
  validateThreadId(trimmedId);

  try {
    // Call DELETE API
    await del(`/threads/${trimmedId}`, {
      token,
    });

    return { success: true };
  } catch (error) {
    // Re-throw API and Network errors as-is
    if (error instanceof ApiError || error instanceof NetworkError) {
      throw error;
    }
    
    // Wrap other errors
    throw new Error('スレッドの削除に失敗しました');
  }
}