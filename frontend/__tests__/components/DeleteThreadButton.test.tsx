import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DeleteThreadButton } from '@/components/DeleteThreadButton';
import * as deleteThreadModule from '@/lib/actions/deleteThread';
import { ApiError } from '@/lib/api';

// Mock next/navigation
const mockPush = vi.fn();
const mockRefresh = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: mockRefresh,
  }),
}));

// Mock deleteThread action
vi.mock('@/lib/actions/deleteThread');

describe('DeleteThreadButton', () => {
  const mockDeleteThread = vi.mocked(deleteThreadModule.deleteThread);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders delete button', () => {
    render(<DeleteThreadButton threadId="thr_01234567890123456789012345" />);
    
    const button = screen.getByRole('button', { name: /削除/ });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('削除');
  });

  it('shows delete dialog when clicked', async () => {
    render(<DeleteThreadButton threadId="thr_01234567890123456789012345" />);
    
    const button = screen.getByRole('button', { name: /削除/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('スレッドの削除')).toBeInTheDocument();
      expect(screen.getByText('このスレッドを削除してもよろしいですか？この操作は取り消せません。')).toBeInTheDocument();
    });
  });

  it('closes dialog when cancel is clicked', async () => {
    render(<DeleteThreadButton threadId="thr_01234567890123456789012345" />);
    
    const button = screen.getByRole('button', { name: /削除/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    const cancelButton = screen.getByText('キャンセル');
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
    
    expect(mockDeleteThread).not.toHaveBeenCalled();
  });

  it('deletes thread and redirects on success', async () => {
    mockDeleteThread.mockResolvedValue({ success: true });
    
    render(<DeleteThreadButton threadId="thr_01234567890123456789012345" />);
    
    // Open dialog
    const button = screen.getByRole('button', { name: /削除/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Click delete in dialog
    const deleteButtons = screen.getAllByText('削除');
    const dialogDeleteButton = deleteButtons[deleteButtons.length - 1]; // Last one is in dialog
    fireEvent.click(dialogDeleteButton);

    await waitFor(() => {
      expect(mockDeleteThread).toHaveBeenCalledWith('thr_01234567890123456789012345');
      expect(mockPush).toHaveBeenCalledWith('/');
      expect(mockRefresh).toHaveBeenCalled();
    });
  });

  it('shows loading state while deleting', async () => {
    mockDeleteThread.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );
    
    render(<DeleteThreadButton threadId="thr_01234567890123456789012345" />);
    
    // Open dialog
    const button = screen.getByRole('button', { name: /削除/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Click delete in dialog
    const deleteButtons = screen.getAllByText('削除');
    const dialogDeleteButton = deleteButtons[deleteButtons.length - 1];
    fireEvent.click(dialogDeleteButton);

    await waitFor(() => {
      expect(screen.getByText('削除中...')).toBeInTheDocument();
    });
  });

  it('handles 403 permission error', async () => {
    mockDeleteThread.mockRejectedValue(new ApiError(
      403,
      'PERMISSION_DENIED',
      'You do not have permission'
    ));
    
    render(<DeleteThreadButton threadId="thr_01234567890123456789012345" />);
    
    // Open dialog
    const button = screen.getByRole('button', { name: /削除/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Click delete in dialog
    const deleteButtons = screen.getAllByText('削除');
    const dialogDeleteButton = deleteButtons[deleteButtons.length - 1];
    fireEvent.click(dialogDeleteButton);

    await waitFor(() => {
      expect(screen.getByText('このスレッドを削除する権限がありません')).toBeInTheDocument();
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it('handles 404 not found error', async () => {
    mockDeleteThread.mockRejectedValue(new ApiError(
      404,
      'NOT_FOUND',
      'Thread not found'
    ));
    
    render(<DeleteThreadButton threadId="thr_01234567890123456789012345" />);
    
    // Open dialog
    const button = screen.getByRole('button', { name: /削除/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Click delete in dialog
    const deleteButtons = screen.getAllByText('削除');
    const dialogDeleteButton = deleteButtons[deleteButtons.length - 1];
    fireEvent.click(dialogDeleteButton);

    await waitFor(() => {
      expect(screen.getByText('スレッドが見つかりません')).toBeInTheDocument();
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it('handles 401 authentication error', async () => {
    mockDeleteThread.mockRejectedValue(new ApiError(
      401,
      'AUTHENTICATION_ERROR',
      'Not authenticated'
    ));
    
    render(<DeleteThreadButton threadId="thr_01234567890123456789012345" />);
    
    // Open dialog
    const button = screen.getByRole('button', { name: /削除/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Click delete in dialog
    const deleteButtons = screen.getAllByText('削除');
    const dialogDeleteButton = deleteButtons[deleteButtons.length - 1];
    fireEvent.click(dialogDeleteButton);

    await waitFor(() => {
      expect(screen.getByText('ログインが必要です')).toBeInTheDocument();
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it('handles generic error', async () => {
    mockDeleteThread.mockRejectedValue(new Error('Network error'));
    
    render(<DeleteThreadButton threadId="thr_01234567890123456789012345" />);
    
    // Open dialog
    const button = screen.getByRole('button', { name: /削除/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Click delete in dialog
    const deleteButtons = screen.getAllByText('削除');
    const dialogDeleteButton = deleteButtons[deleteButtons.length - 1];
    fireEvent.click(dialogDeleteButton);

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(mockPush).not.toHaveBeenCalled();
    });
  });
});