import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DeleteConfirmDialog } from '@/components/DeleteConfirmDialog';

describe('DeleteConfirmDialog', () => {
  const mockOnConfirm = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when closed', () => {
    const { container } = render(
      <DeleteConfirmDialog
        isOpen={false}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    expect(container.firstChild).toBeNull();
  });

  it('renders dialog when open', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('削除の確認')).toBeInTheDocument();
    expect(screen.getByText('この操作は取り消せません。本当に削除しますか？')).toBeInTheDocument();
  });

  it('renders with custom props', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        title="Custom Title"
        message="Custom message"
        confirmLabel="Remove"
        cancelLabel="Back"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
    expect(screen.getByText('Custom message')).toBeInTheDocument();
    expect(screen.getByText('Remove')).toBeInTheDocument();
    expect(screen.getByText('Back')).toBeInTheDocument();
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    const cancelButton = screen.getByText('キャンセル');
    fireEvent.click(cancelButton);
    
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
    expect(mockOnConfirm).not.toHaveBeenCalled();
  });

  it('calls onCancel when close button is clicked', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    const closeButton = screen.getByLabelText('閉じる');
    fireEvent.click(closeButton);
    
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
    expect(mockOnConfirm).not.toHaveBeenCalled();
  });

  it('calls onConfirm when delete button is clicked', async () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    const deleteButton = screen.getByText('削除');
    fireEvent.click(deleteButton);
    
    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledTimes(1);
    });
    expect(mockOnCancel).not.toHaveBeenCalled();
  });

  it('shows loading state during async operation', async () => {
    mockOnConfirm.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );
    
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    const deleteButton = screen.getByText('削除');
    fireEvent.click(deleteButton);
    
    // Should show loading state
    await waitFor(() => {
      expect(screen.getByText('削除中...')).toBeInTheDocument();
    });
    
    // Buttons should be disabled
    expect(screen.getByText('キャンセル')).toBeDisabled();
    expect(screen.getByLabelText('閉じる')).toBeDisabled();
  });

  it('shows error message when confirmation fails', async () => {
    const errorMessage = 'Failed to delete';
    mockOnConfirm.mockRejectedValue(new Error(errorMessage));
    
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    const deleteButton = screen.getByText('削除');
    fireEvent.click(deleteButton);
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
    
    // Should re-enable buttons after error
    expect(screen.getByText('キャンセル')).not.toBeDisabled();
    expect(screen.getByText('削除')).not.toBeDisabled();
  });

  it('closes on ESC key press', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
    expect(mockOnConfirm).not.toHaveBeenCalled();
  });

  it('does not close on ESC when deleting', async () => {
    mockOnConfirm.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );
    
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    const deleteButton = screen.getByText('削除');
    fireEvent.click(deleteButton);
    
    // Wait for loading state
    await waitFor(() => {
      expect(screen.getByText('削除中...')).toBeInTheDocument();
    });
    
    // ESC should not close during deletion
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });
    expect(mockOnCancel).not.toHaveBeenCalled();
  });

  it('has proper ARIA attributes', () => {
    render(
      <DeleteConfirmDialog
        isOpen={true}
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
      />
    );
    
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'dialog-title');
    expect(dialog).toHaveAttribute('aria-describedby', 'dialog-message');
  });
});