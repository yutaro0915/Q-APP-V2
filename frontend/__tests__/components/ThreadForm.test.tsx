import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThreadForm } from '@/components/ThreadForm';

describe('ThreadForm', () => {
  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all form fields', () => {
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    expect(screen.getByLabelText(/タイトル/)).toBeInTheDocument();
    expect(screen.getByLabelText(/本文/)).toBeInTheDocument();
    expect(screen.getByText('タグ')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '投稿する' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'キャンセル' })).toBeInTheDocument();
  });

  it('displays character counter for title', async () => {
    const user = userEvent.setup();
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    const titleInput = screen.getByLabelText(/タイトル/);
    await user.type(titleInput, 'Test Title');
    
    expect(screen.getByText('10 / 60')).toBeInTheDocument();
  });

  it('displays character counter for body', async () => {
    const user = userEvent.setup();
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    const bodyInput = screen.getByLabelText(/本文/);
    await user.type(bodyInput, 'Test body content');
    
    expect(screen.getByText('17 / 2000')).toBeInTheDocument();
  });

  it('validates title is required', async () => {
    const user = userEvent.setup();
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    const submitButton = screen.getByRole('button', { name: '投稿する' });
    await user.click(submitButton);
    
    expect(screen.getByText('タイトルは必須です')).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });


  it('trims title before validation', async () => {
    const user = userEvent.setup();
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    const titleInput = screen.getByLabelText(/タイトル/);
    await user.type(titleInput, '  Test Title  ');
    
    const submitButton = screen.getByRole('button', { name: '投稿する' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        title: 'Test Title',
        body: '',
        tags: [],
        imageKey: null
      });
    });
  });

  it('allows adding tags', async () => {
    const user = userEvent.setup();
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    // Add 種別 tag
    const typeSelect = screen.getByLabelText(/種別/);
    await user.selectOptions(typeSelect, 'question');
    
    // Add 場所 tag
    const locationInput = screen.getByLabelText(/場所/);
    await user.type(locationInput, '伊都キャンパス');
    
    // Check that tags are shown (using more specific selector for tag display)
    const tagElements = screen.getAllByText('質問');
    expect(tagElements.length).toBeGreaterThan(0);
    expect(screen.getByDisplayValue('伊都キャンパス')).toBeInTheDocument();
  });

  it('validates maximum 4 tags', async () => {
    const user = userEvent.setup();
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    // Try to add all tags
    await user.selectOptions(screen.getByLabelText(/種別/), 'question');
    await user.type(screen.getByLabelText(/場所/), '伊都キャンパス');
    await user.type(screen.getByLabelText(/締切/), '2024-12-31');
    await user.type(screen.getByLabelText(/授業コード/), 'CS101');
    
    // All 4 tags should be added
    const titleInput = screen.getByLabelText(/タイトル/);
    await user.type(titleInput, 'Test Title');
    
    const submitButton = screen.getByRole('button', { name: '投稿する' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          tags: expect.arrayContaining([
            { key: '種別', value: 'question' },
            { key: '場所', value: '伊都キャンパス' },
            { key: '締切', value: '2024-12-31' },
            { key: '授業コード', value: 'CS101' }
          ])
        })
      );
    });
  });

  it('prevents duplicate tag keys', async () => {
    const user = userEvent.setup();
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    // Add 種別 tag
    const typeSelect = screen.getByLabelText(/種別/);
    await user.selectOptions(typeSelect, 'question');
    
    // Try to change 種別 tag
    await user.selectOptions(typeSelect, 'notice');
    
    // Should only have one 種別 tag with latest value (check in tags display area)
    const tagSpans = document.querySelectorAll('.inline-block.px-2.py-1.text-xs.bg-gray-100.text-gray-700.rounded');
    const tagTexts = Array.from(tagSpans).map(span => span.textContent);
    expect(tagTexts).toContain('告知');
    expect(tagTexts).not.toContain('質問');
  });

  it('removes tags when cleared', async () => {
    const user = userEvent.setup();
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    // Add a tag
    const typeSelect = screen.getByLabelText(/種別/);
    await user.selectOptions(typeSelect, 'question');
    
    // Verify tag is shown
    const tagSpansInitial = document.querySelectorAll('.inline-block.px-2.py-1.text-xs.bg-gray-100.text-gray-700.rounded');
    const tagTextsInitial = Array.from(tagSpansInitial).map(span => span.textContent);
    expect(tagTextsInitial).toContain('質問');
    
    // Clear the tag
    await user.selectOptions(typeSelect, '');
    
    // Verify tag is removed
    const tagSpansAfter = document.querySelectorAll('.inline-block.px-2.py-1.text-xs.bg-gray-100.text-gray-700.rounded');
    const tagTextsAfter = Array.from(tagSpansAfter).map(span => span.textContent);
    expect(tagTextsAfter).not.toContain('質問');
  });

  it('disables submit button while submitting', async () => {
    const user = userEvent.setup();
    let resolveSubmit: () => void;
    const submitPromise = new Promise<void>((resolve) => {
      resolveSubmit = resolve;
    });
    
    mockOnSubmit.mockReturnValue(submitPromise);
    
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    const titleInput = screen.getByLabelText(/タイトル/);
    await user.type(titleInput, 'Test Title');
    
    const submitButton = screen.getByRole('button', { name: '投稿する' });
    await user.click(submitButton);
    
    // Button should be disabled during submission
    expect(submitButton).toBeDisabled();
    expect(screen.getByText('投稿中...')).toBeInTheDocument();
    
    // Resolve the promise
    resolveSubmit!();
    
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
      expect(screen.getByRole('button', { name: '投稿する' })).toBeInTheDocument();
    });
  });

  it('shows error message on submission failure', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockRejectedValue(new Error('投稿に失敗しました'));
    
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    const titleInput = screen.getByLabelText(/タイトル/);
    await user.type(titleInput, 'Test Title');
    
    const submitButton = screen.getByRole('button', { name: '投稿する' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('投稿に失敗しました')).toBeInTheDocument();
    });
  });

  it('resets form after successful submission', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);
    
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    const titleInput = screen.getByLabelText(/タイトル/) as HTMLInputElement;
    const bodyInput = screen.getByLabelText(/本文/) as HTMLTextAreaElement;
    
    await user.type(titleInput, 'Test Title');
    await user.type(bodyInput, 'Test Body');
    
    const submitButton = screen.getByRole('button', { name: '投稿する' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(titleInput.value).toBe('');
      expect(bodyInput.value).toBe('');
    });
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    const cancelButton = screen.getByRole('button', { name: 'キャンセル' });
    await user.click(cancelButton);
    
    expect(mockOnCancel).toHaveBeenCalled();
  });


  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);
    
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    // Fill in form
    await user.type(screen.getByLabelText(/タイトル/), 'Test Thread Title');
    await user.type(screen.getByLabelText(/本文/), 'This is the thread body content');
    await user.selectOptions(screen.getByLabelText(/種別/), 'question');
    await user.type(screen.getByLabelText(/場所/), '伊都キャンパス');
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: '投稿する' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        title: 'Test Thread Title',
        body: 'This is the thread body content',
        tags: [
          { key: '種別', value: 'question' },
          { key: '場所', value: '伊都キャンパス' }
        ],
        imageKey: null
      });
    });
  });

  it('handles empty body as empty string', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);
    
    render(<ThreadForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
    
    await user.type(screen.getByLabelText(/タイトル/), 'Test Title');
    
    const submitButton = screen.getByRole('button', { name: '投稿する' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          body: ''
        })
      );
    });
  });
});