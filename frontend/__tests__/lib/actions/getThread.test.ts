import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getThread, getThreadWithAuth } from '@/lib/actions/getThread';
import * as api from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api');

describe('getThread', () => {
  const mockGet = vi.mocked(api.get);
  
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockThread = {
    id: 'thr_01234567890123456789012345',
    authorId: 'usr_12345678901234567890123456',
    title: 'Test Thread',
    body: 'This is a test thread body',
    tags: [{ key: 'test', name: 'Test' }],
    imageKey: undefined,
    solvedCommentId: undefined,
    upCount: 5,
    saveCount: 2,
    heat: 10,
    isMine: false,
    createdAt: '2024-01-01T00:00:00Z',
    lastActivityAt: '2024-01-01T00:00:00Z',
    authorProfile: {
      displayName: 'Test User',
      iconKind: 'default',
    },
    authorAffiliation: {
      faculty: '工学部',
      year: 3,
    },
  };

  describe('getThread (without auth)', () => {
    it('fetches thread successfully', async () => {
      mockGet.mockResolvedValue(mockThread);

      const threadId = 'thr_01234567890123456789012345';
      const result = await getThread(threadId);

      expect(mockGet).toHaveBeenCalledWith(`/threads/${threadId}`);
      expect(result).toEqual(mockThread);
    });

    it('validates thread ID format', async () => {
      // Invalid thread ID format
      await expect(getThread('invalid-id')).rejects.toThrow('無効なスレッドIDです');
      await expect(getThread('')).rejects.toThrow('スレッドIDが必要です');
      await expect(getThread('usr_01234567890123456789012345')).rejects.toThrow('無効なスレッドIDです');
      
      expect(mockGet).not.toHaveBeenCalled();
    });

    it('trims thread ID', async () => {
      mockGet.mockResolvedValue(mockThread);

      const threadId = '  thr_01234567890123456789012345  ';
      await getThread(threadId);

      expect(mockGet).toHaveBeenCalledWith('/threads/thr_01234567890123456789012345');
    });

    it('handles 404 not found error', async () => {
      mockGet.mockRejectedValue(new api.ApiError(
        404,
        'NOT_FOUND',
        'Thread not found',
        undefined,
        'req_123'
      ));

      const threadId = 'thr_01234567890123456789012345';

      await expect(getThread(threadId)).rejects.toThrow(api.ApiError);
      expect(mockGet).toHaveBeenCalled();
    });

    it('handles network errors', async () => {
      mockGet.mockRejectedValue(new api.NetworkError('Network request failed'));

      const threadId = 'thr_01234567890123456789012345';

      await expect(getThread(threadId)).rejects.toThrow(api.NetworkError);
      expect(mockGet).toHaveBeenCalled();
    });

    it('wraps unknown errors', async () => {
      mockGet.mockRejectedValue(new Error('Unknown error'));

      const threadId = 'thr_01234567890123456789012345';

      await expect(getThread(threadId)).rejects.toThrow('スレッドの取得に失敗しました');
      expect(mockGet).toHaveBeenCalled();
    });
  });

  describe('getThreadWithAuth', () => {
    it('fetches thread with authentication', async () => {
      const threadWithAuth = { ...mockThread, isMine: true };
      mockGet.mockResolvedValue(threadWithAuth);

      const threadId = 'thr_01234567890123456789012345';
      const token = 'test-token';
      const result = await getThreadWithAuth(threadId, token);

      expect(mockGet).toHaveBeenCalledWith(`/threads/${threadId}`, { token });
      expect(result).toEqual(threadWithAuth);
    });

    it('fetches thread without token', async () => {
      mockGet.mockResolvedValue(mockThread);

      const threadId = 'thr_01234567890123456789012345';
      const result = await getThreadWithAuth(threadId);

      expect(mockGet).toHaveBeenCalledWith(`/threads/${threadId}`, { token: undefined });
      expect(result).toEqual(mockThread);
    });

    it('validates thread ID format', async () => {
      const token = 'test-token';
      
      await expect(getThreadWithAuth('invalid-id', token)).rejects.toThrow('無効なスレッドIDです');
      await expect(getThreadWithAuth('', token)).rejects.toThrow('スレッドIDが必要です');
      
      expect(mockGet).not.toHaveBeenCalled();
    });

    it('handles 401 authentication error', async () => {
      mockGet.mockRejectedValue(new api.ApiError(
        401,
        'AUTHENTICATION_ERROR',
        'Invalid token',
        undefined,
        'req_123'
      ));

      const threadId = 'thr_01234567890123456789012345';
      const token = 'invalid-token';

      await expect(getThreadWithAuth(threadId, token)).rejects.toThrow(api.ApiError);
      expect(mockGet).toHaveBeenCalled();
    });

    it('handles network errors', async () => {
      mockGet.mockRejectedValue(new api.NetworkError('Network request failed'));

      const threadId = 'thr_01234567890123456789012345';
      const token = 'test-token';

      await expect(getThreadWithAuth(threadId, token)).rejects.toThrow(api.NetworkError);
      expect(mockGet).toHaveBeenCalled();
    });
  });
});