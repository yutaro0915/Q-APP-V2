import { describe, it, expect, vi, beforeEach } from 'vitest';
import { deleteThread } from '@/lib/actions/deleteThread';
import * as api from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api');

describe('deleteThread', () => {
  const mockDel = vi.mocked(api.del);
  
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    const localStorageMock: Storage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
      key: vi.fn(),
      length: 0,
    };
    global.localStorage = localStorageMock;
  });

  it('deletes a thread successfully', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );
    mockDel.mockResolvedValue(null);

    const threadId = 'thr_01234567890123456789012345';
    
    await deleteThread(threadId);

    expect(mockDel).toHaveBeenCalledWith(`/threads/${threadId}`, {
      token: 'test-token',
    });
  });

  it('validates thread ID format', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );

    // Invalid thread ID format
    await expect(deleteThread('invalid-id')).rejects.toThrow('無効なスレッドIDです');
    await expect(deleteThread('')).rejects.toThrow('スレッドIDが必要です');
    await expect(deleteThread('usr_01234567890123456789012345')).rejects.toThrow('無効なスレッドIDです');
    
    expect(mockDel).not.toHaveBeenCalled();
  });

  it('handles no auth token', async () => {
    vi.mocked(localStorage.getItem).mockImplementation(() => null);

    const threadId = 'thr_01234567890123456789012345';

    await expect(deleteThread(threadId)).rejects.toThrow('認証が必要です');
    expect(mockDel).not.toHaveBeenCalled();
  });

  it('handles 401 authentication error', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );
    mockDel.mockRejectedValue(new api.ApiError(
      401,
      'AUTHENTICATION_ERROR',
      'Token expired',
      undefined,
      'req_123'
    ));

    const threadId = 'thr_01234567890123456789012345';

    await expect(deleteThread(threadId)).rejects.toThrow(api.ApiError);
    expect(mockDel).toHaveBeenCalled();
  });

  it('handles 403 permission error', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );
    mockDel.mockRejectedValue(new api.ApiError(
      403,
      'PERMISSION_DENIED',
      'You do not have permission to delete this thread',
      undefined,
      'req_123'
    ));

    const threadId = 'thr_01234567890123456789012345';

    await expect(deleteThread(threadId)).rejects.toThrow(api.ApiError);
    expect(mockDel).toHaveBeenCalled();
  });

  it('handles 404 not found error', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );
    mockDel.mockRejectedValue(new api.ApiError(
      404,
      'NOT_FOUND',
      'Thread not found',
      undefined,
      'req_123'
    ));

    const threadId = 'thr_01234567890123456789012345';

    await expect(deleteThread(threadId)).rejects.toThrow(api.ApiError);
    expect(mockDel).toHaveBeenCalled();
  });

  it('handles network errors', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );
    mockDel.mockRejectedValue(new api.NetworkError('Network request failed'));

    const threadId = 'thr_01234567890123456789012345';

    await expect(deleteThread(threadId)).rejects.toThrow(api.NetworkError);
    expect(mockDel).toHaveBeenCalled();
  });

  it('returns success result', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );
    mockDel.mockResolvedValue(null);

    const threadId = 'thr_01234567890123456789012345';
    
    const result = await deleteThread(threadId);

    expect(result).toEqual({ success: true });
    expect(mockDel).toHaveBeenCalledWith(`/threads/${threadId}`, {
      token: 'test-token',
    });
  });

  it('trims thread ID', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );
    mockDel.mockResolvedValue(null);

    const threadId = '  thr_01234567890123456789012345  ';
    
    await deleteThread(threadId);

    expect(mockDel).toHaveBeenCalledWith('/threads/thr_01234567890123456789012345', {
      token: 'test-token',
    });
  });
});