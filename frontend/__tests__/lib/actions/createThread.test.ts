import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createThread } from '@/lib/actions/createThread';
import * as api from '@/lib/api';

// Mock the API module
vi.mock('@/lib/api');

describe('createThread', () => {
  const mockPost = vi.mocked(api.post);
  
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

  it('creates a thread successfully', async () => {
    const mockThread = {
      id: 'thr_01234567890123456789012345',
      title: 'Test Thread',
      body: 'Test body content',
      tags: [{ key: '種別', value: 'question' }],
      authorId: 'usr_01234567890123456789012345',
      upCount: 0,
      saveCount: 0,
      heat: 0,
      replies: 0,
      saves: 0,
      createdAt: '2024-01-01T00:00:00Z',
      lastActivityAt: '2024-01-01T00:00:00Z',
      solvedCommentId: null,
      hasImage: false,
      imageThumbUrl: null,
      solved: false,
      authorAffiliation: null,
      isMine: true,
    };

    mockPost.mockResolvedValue(mockThread);
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );

    const formData = {
      title: 'Test Thread',
      body: 'Test body content',
      tags: [{ key: '種別', value: 'question' }],
      imageKey: null,
    };

    const result = await createThread(formData);

    expect(mockPost).toHaveBeenCalledWith('/threads', formData, {
      token: 'test-token',
    });
    expect(result).toEqual(mockThread);
  });

  it('trims title and body before sending', async () => {
    const mockThread = {
      id: 'thr_01234567890123456789012345',
      title: 'Test Thread',
      body: 'Test body',
      tags: [],
      authorId: 'usr_01234567890123456789012345',
      upCount: 0,
      saveCount: 0,
      heat: 0,
      replies: 0,
      saves: 0,
      createdAt: '2024-01-01T00:00:00Z',
      lastActivityAt: '2024-01-01T00:00:00Z',
      solvedCommentId: null,
      hasImage: false,
      imageThumbUrl: null,
      solved: false,
      authorAffiliation: null,
      isMine: true,
    };

    mockPost.mockResolvedValue(mockThread);
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );

    const formData = {
      title: '  Test Thread  ',
      body: '  Test body  ',
      tags: [],
      imageKey: null,
    };

    await createThread(formData);

    expect(mockPost).toHaveBeenCalledWith('/threads', {
      title: 'Test Thread',
      body: 'Test body',
      tags: [],
      imageKey: null,
    }, {
      token: 'test-token',
    });
  });

  it('validates title is required', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );

    const formData = {
      title: '',
      body: 'Test body',
      tags: [],
      imageKey: null,
    };

    await expect(createThread(formData)).rejects.toThrow('タイトルは必須です');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('validates title max length', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );

    const formData = {
      title: 'a'.repeat(61),
      body: 'Test body',
      tags: [],
      imageKey: null,
    };

    await expect(createThread(formData)).rejects.toThrow('タイトルは60文字以内で入力してください');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('validates body max length', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );

    const formData = {
      title: 'Test Title',
      body: 'a'.repeat(2001),
      tags: [],
      imageKey: null,
    };

    await expect(createThread(formData)).rejects.toThrow('本文は2000文字以内で入力してください');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('validates max 4 tags', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );

    const formData = {
      title: 'Test Title',
      body: 'Test body',
      tags: [
        { key: '種別', value: 'question' },
        { key: '場所', value: '伊都' },
        { key: '締切', value: '2024-12-31' },
        { key: '授業コード', value: 'CS101' },
        { key: 'extra', value: 'invalid' },
      ],
      imageKey: null,
    };

    await expect(createThread(formData)).rejects.toThrow('タグは最大4つまでです');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('validates unique tag keys', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );

    const formData = {
      title: 'Test Title',
      body: 'Test body',
      tags: [
        { key: '種別', value: 'question' },
        { key: '種別', value: 'notice' },
      ],
      imageKey: null,
    };

    await expect(createThread(formData)).rejects.toThrow('タグのキーが重複しています');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('handles no auth token', async () => {
    vi.mocked(localStorage.getItem).mockImplementation(() => null);

    const formData = {
      title: 'Test Title',
      body: 'Test body',
      tags: [],
      imageKey: null,
    };

    await expect(createThread(formData)).rejects.toThrow('認証が必要です');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('handles API errors', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );
    mockPost.mockRejectedValue(new api.ApiError(
      400,
      'VALIDATION_ERROR',
      'Invalid request',
      [{ field: 'title', reason: 'required' }],
      'req_123'
    ));

    const formData = {
      title: 'Test Title',
      body: 'Test body',
      tags: [],
      imageKey: null,
    };

    await expect(createThread(formData)).rejects.toThrow(api.ApiError);
    expect(mockPost).toHaveBeenCalled();
  });

  it('handles network errors', async () => {
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );
    mockPost.mockRejectedValue(new api.NetworkError('Network request failed'));

    const formData = {
      title: 'Test Title',
      body: 'Test body',
      tags: [],
      imageKey: null,
    };

    await expect(createThread(formData)).rejects.toThrow(api.NetworkError);
    expect(mockPost).toHaveBeenCalled();
  });

  it('allows empty body', async () => {
    const mockThread = {
      id: 'thr_01234567890123456789012345',
      title: 'Test Thread',
      body: '',
      tags: [],
      authorId: 'usr_01234567890123456789012345',
      upCount: 0,
      saveCount: 0,
      heat: 0,
      replies: 0,
      saves: 0,
      createdAt: '2024-01-01T00:00:00Z',
      lastActivityAt: '2024-01-01T00:00:00Z',
      solvedCommentId: null,
      hasImage: false,
      imageThumbUrl: null,
      solved: false,
      authorAffiliation: null,
      isMine: true,
    };

    mockPost.mockResolvedValue(mockThread);
    vi.mocked(localStorage.getItem).mockImplementation((key) => 
      key === 'auth_token' ? 'test-token' : null
    );

    const formData = {
      title: 'Test Thread',
      body: '',
      tags: [],
      imageKey: null,
    };

    const result = await createThread(formData);

    expect(mockPost).toHaveBeenCalledWith('/threads', formData, {
      token: 'test-token',
    });
    expect(result).toEqual(mockThread);
  });
});