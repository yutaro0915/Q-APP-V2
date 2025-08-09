import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getThreads, getThreadsWithAuth } from '@/lib/actions/getThreads';
import * as api from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api');

describe('getThreads', () => {
  const mockGet = vi.mocked(api.get);
  
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockThreadsResponse = {
    threads: [
      {
        id: 'thr_01234567890123456789012345',
        authorId: 'usr_12345678901234567890123456',
        title: 'Test Thread 1',
        body: 'This is the first test thread body',
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
      },
      {
        id: 'thr_01234567890123456789012346',
        authorId: 'usr_12345678901234567890123457',
        title: 'Test Thread 2',
        body: 'This is the second test thread body',
        tags: [{ key: 'question', name: '質問' }],
        imageKey: 'img_12345',
        solvedCommentId: 'cmt_12345',
        upCount: 10,
        saveCount: 5,
        heat: 20,
        isMine: false,
        createdAt: '2024-01-02T00:00:00Z',
        lastActivityAt: '2024-01-02T12:00:00Z',
        authorProfile: {
          displayName: 'Another User',
          iconKind: 'default',
        },
        authorAffiliation: null,
      },
    ],
    nextCursor: 'eyJjcmVhdGVkQXQiOiIyMDI0LTAxLTAyVDAwOjAwOjAwWiIsImlkIjoidGhyXzAxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ2In0=',
  };

  describe('getThreads (without auth)', () => {
    it('fetches threads with default sort (new)', async () => {
      mockGet.mockResolvedValue(mockThreadsResponse);

      const result = await getThreads();

      expect(mockGet).toHaveBeenCalledWith('/threads', {
        params: { sort: 'new' },
      });
      expect(result).toEqual(mockThreadsResponse);
    });

    it('fetches threads with hot sort', async () => {
      mockGet.mockResolvedValue(mockThreadsResponse);

      const result = await getThreads('hot');

      expect(mockGet).toHaveBeenCalledWith('/threads', {
        params: { sort: 'hot' },
      });
      expect(result).toEqual(mockThreadsResponse);
    });

    it('fetches threads with cursor for pagination', async () => {
      mockGet.mockResolvedValue(mockThreadsResponse);

      const cursor = 'eyJjcmVhdGVkQXQiOiIyMDI0LTAxLTAxVDAwOjAwOjAwWiIsImlkIjoidGhyXzEyMyJ9';
      const result = await getThreads('new', cursor);

      expect(mockGet).toHaveBeenCalledWith('/threads', {
        params: { sort: 'new', cursor },
      });
      expect(result).toEqual(mockThreadsResponse);
    });

    it('handles empty response', async () => {
      const emptyResponse = { threads: [], nextCursor: undefined };
      mockGet.mockResolvedValue(emptyResponse);

      const result = await getThreads();

      expect(mockGet).toHaveBeenCalledWith('/threads', {
        params: { sort: 'new' },
      });
      expect(result).toEqual(emptyResponse);
    });

    it('handles API errors', async () => {
      mockGet.mockRejectedValue(new api.ApiError(
        500,
        'SERVER_ERROR',
        'Internal server error',
        undefined,
        'req_123'
      ));

      await expect(getThreads()).rejects.toThrow(api.ApiError);
      expect(mockGet).toHaveBeenCalled();
    });

    it('handles network errors', async () => {
      mockGet.mockRejectedValue(new api.NetworkError('Network request failed'));

      await expect(getThreads()).rejects.toThrow(api.NetworkError);
      expect(mockGet).toHaveBeenCalled();
    });

    it('wraps unknown errors', async () => {
      mockGet.mockRejectedValue(new Error('Unknown error'));

      await expect(getThreads()).rejects.toThrow('スレッド一覧の取得に失敗しました');
      expect(mockGet).toHaveBeenCalled();
    });
  });

  describe('getThreadsWithAuth', () => {
    it('fetches threads with authentication', async () => {
      const responseWithAuth = {
        ...mockThreadsResponse,
        threads: mockThreadsResponse.threads.map((t, i) => ({
          ...t,
          isMine: i === 0, // First thread is mine
        })),
      };
      mockGet.mockResolvedValue(responseWithAuth);

      const token = 'test-token';
      const result = await getThreadsWithAuth('new', undefined, token);

      expect(mockGet).toHaveBeenCalledWith('/threads', {
        params: { sort: 'new' },
        token,
      });
      expect(result).toEqual(responseWithAuth);
    });

    it('fetches threads without token', async () => {
      mockGet.mockResolvedValue(mockThreadsResponse);

      const result = await getThreadsWithAuth();

      expect(mockGet).toHaveBeenCalledWith('/threads', {
        params: { sort: 'new' },
        token: undefined,
      });
      expect(result).toEqual(mockThreadsResponse);
    });

    it('fetches threads with hot sort and cursor', async () => {
      mockGet.mockResolvedValue(mockThreadsResponse);

      const token = 'test-token';
      const cursor = 'eyJjcmVhdGVkQXQiOiIyMDI0LTAxLTAxVDAwOjAwOjAwWiIsImlkIjoidGhyXzEyMyJ9';
      const result = await getThreadsWithAuth('hot', cursor, token);

      expect(mockGet).toHaveBeenCalledWith('/threads', {
        params: { sort: 'hot', cursor },
        token,
      });
      expect(result).toEqual(mockThreadsResponse);
    });

    it('handles 401 authentication error', async () => {
      mockGet.mockRejectedValue(new api.ApiError(
        401,
        'AUTHENTICATION_ERROR',
        'Invalid token',
        undefined,
        'req_123'
      ));

      const token = 'invalid-token';
      await expect(getThreadsWithAuth('new', undefined, token)).rejects.toThrow(api.ApiError);
      expect(mockGet).toHaveBeenCalled();
    });

    it('handles network errors', async () => {
      mockGet.mockRejectedValue(new api.NetworkError('Network request failed'));

      const token = 'test-token';
      await expect(getThreadsWithAuth('new', undefined, token)).rejects.toThrow(api.NetworkError);
      expect(mockGet).toHaveBeenCalled();
    });
  });
});