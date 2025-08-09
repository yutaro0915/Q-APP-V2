/**
 * Create thread action
 * Client-side helper function for creating threads
 */

import { post, ApiError, NetworkError } from '@/lib/api';

// Types
export interface ThreadTag {
  key: string;
  value: string;
}

export interface CreateThreadData {
  title: string;
  body: string;
  tags: ThreadTag[];
  imageKey: string | null;
}

export interface Thread {
  id: string;
  title: string;
  body: string;
  tags: ThreadTag[];
  authorId: string;
  upCount: number;
  saveCount: number;
  heat: number;
  replies: number;
  saves: number;
  createdAt: string;
  lastActivityAt: string;
  solvedCommentId: string | null;
  hasImage: boolean;
  imageThumbUrl: string | null;
  solved: boolean;
  authorAffiliation: {
    faculty: string | null;
    year: number | null;
  } | null;
  isMine: boolean;
}

/**
 * Validate thread creation data
 */
function validateThreadData(data: CreateThreadData): void {
  // Trim strings for validation
  const trimmedTitle = data.title.trim();
  const trimmedBody = data.body.trim();

  // Title validation
  if (!trimmedTitle) {
    throw new Error('タイトルは必須です');
  }
  if (trimmedTitle.length > 60) {
    throw new Error('タイトルは60文字以内で入力してください');
  }

  // Body validation
  if (trimmedBody.length > 2000) {
    throw new Error('本文は2000文字以内で入力してください');
  }

  // Tags validation
  if (data.tags.length > 4) {
    throw new Error('タグは最大4つまでです');
  }

  // Check for duplicate tag keys
  const tagKeys = new Set<string>();
  for (const tag of data.tags) {
    if (tagKeys.has(tag.key)) {
      throw new Error('タグのキーが重複しています');
    }
    tagKeys.add(tag.key);
  }
}

/**
 * Create a new thread
 * @param data Thread creation data
 * @returns Created thread object
 * @throws {Error} Validation error
 * @throws {ApiError} API error response
 * @throws {NetworkError} Network error
 */
export async function createThread(data: CreateThreadData): Promise<Thread> {
  // Get auth token from localStorage
  const token = localStorage.getItem('auth_token');
  if (!token) {
    throw new Error('認証が必要です');
  }

  // Validate input data
  validateThreadData(data);

  // Prepare request data with trimmed values
  const requestData: CreateThreadData = {
    title: data.title.trim(),
    body: data.body.trim(),
    tags: data.tags,
    imageKey: data.imageKey,
  };

  try {
    // Call API
    const thread = await post<Thread>('/threads', requestData, {
      token,
    });

    return thread;
  } catch (error) {
    // Re-throw API and Network errors as-is
    if (error instanceof ApiError || error instanceof NetworkError) {
      throw error;
    }
    
    // Wrap other errors
    throw new Error('スレッドの作成に失敗しました');
  }
}