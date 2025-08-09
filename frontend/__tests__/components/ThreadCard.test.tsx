import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThreadCard } from '@/components/ThreadCard';

describe('ThreadCard', () => {
  const mockThread = {
    id: 'thr_01HX123456789ABCDEFGHJKMNP',
    title: 'Test Thread Title',
    excerpt: 'This is a test excerpt for the thread card component',
    tags: [
      { key: '種別', value: 'question' },
      { key: '場所', value: '伊都キャンパス' }
    ],
    heat: 42,
    replies: 5,
    saves: 3,
    createdAt: '2024-01-01T00:00:00Z',
    lastReplyAt: '2024-01-02T00:00:00Z',
    hasImage: false,
    imageThumbUrl: null,
    solved: false,
    authorAffiliation: {
      faculty: '工学部',
      year: 3
    },
    isMine: false
  };

  it('renders thread title', () => {
    render(<ThreadCard thread={mockThread} />);
    expect(screen.getByText('Test Thread Title')).toBeInTheDocument();
  });

  it('renders thread excerpt', () => {
    render(<ThreadCard thread={mockThread} />);
    expect(screen.getByText('This is a test excerpt for the thread card component')).toBeInTheDocument();
  });

  it('truncates long excerpt with ellipsis', () => {
    const longThread = {
      ...mockThread,
      excerpt: 'a'.repeat(150) // 150 characters
    };
    render(<ThreadCard thread={longThread} />);
    const excerpt = screen.getByTestId('thread-excerpt');
    expect(excerpt.textContent).toContain('…');
  });

  it('displays tags', () => {
    render(<ThreadCard thread={mockThread} />);
    expect(screen.getByText('質問')).toBeInTheDocument();
    expect(screen.getByText('伊都キャンパス')).toBeInTheDocument();
  });

  it('displays metadata counts', () => {
    render(<ThreadCard thread={mockThread} />);
    expect(screen.getByText('5')).toBeInTheDocument(); // replies
    expect(screen.getByText('3')).toBeInTheDocument(); // saves
  });

  it('shows solved badge for solved threads', () => {
    const solvedThread = {
      ...mockThread,
      solved: true,
      tags: [{ key: '種別', value: 'question' }]
    };
    render(<ThreadCard thread={solvedThread} />);
    expect(screen.getByText('解決済み')).toBeInTheDocument();
  });

  it('applies correct color for question type', () => {
    render(<ThreadCard thread={mockThread} />);
    const card = screen.getByTestId('thread-card');
    expect(card.className).toContain('border-blue-500');
  });

  it('applies correct color for notice type', () => {
    const noticeThread = {
      ...mockThread,
      tags: [{ key: '種別', value: 'notice' }]
    };
    render(<ThreadCard thread={noticeThread} />);
    const card = screen.getByTestId('thread-card');
    expect(card.className).toContain('border-orange-500');
  });

  it('applies correct color for recruit type', () => {
    const recruitThread = {
      ...mockThread,
      tags: [{ key: '種別', value: 'recruit' }]
    };
    render(<ThreadCard thread={recruitThread} />);
    const card = screen.getByTestId('thread-card');
    expect(card.className).toContain('border-green-500');
  });

  it('applies correct color for chat type', () => {
    const chatThread = {
      ...mockThread,
      tags: [{ key: '種別', value: 'chat' }]
    };
    render(<ThreadCard thread={chatThread} />);
    const card = screen.getByTestId('thread-card');
    expect(card.className).toContain('border-gray-500');
  });

  it('shows relative time for recent posts', () => {
    const recentThread = {
      ...mockThread,
      createdAt: new Date(Date.now() - 1000 * 60 * 30).toISOString() // 30 minutes ago
    };
    render(<ThreadCard thread={recentThread} />);
    expect(screen.getByText(/30分前/)).toBeInTheDocument();
  });

  it('shows absolute date for old posts', () => {
    render(<ThreadCard thread={mockThread} />);
    expect(screen.getByText(/2024年1月1日/)).toBeInTheDocument();
  });

  it('shows last reply time when available', () => {
    render(<ThreadCard thread={mockThread} />);
    expect(screen.getByText(/最終返信/)).toBeInTheDocument();
  });

  it('does not show last reply when not available', () => {
    const threadWithoutReply = {
      ...mockThread,
      lastReplyAt: null
    };
    render(<ThreadCard thread={threadWithoutReply} />);
    expect(screen.queryByText(/最終返信/)).not.toBeInTheDocument();
  });

  it('has correct link to thread detail', () => {
    render(<ThreadCard thread={mockThread} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/threads/thr_01HX123456789ABCDEFGHJKMNP');
  });

  it('has appropriate aria-label', () => {
    render(<ThreadCard thread={mockThread} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('aria-label', expect.stringContaining('Test Thread Title'));
  });

  it('displays author affiliation when available', () => {
    render(<ThreadCard thread={mockThread} />);
    expect(screen.getByText('工学部 3年')).toBeInTheDocument();
  });

  it('does not display author affiliation when not available', () => {
    const threadWithoutAffiliation = {
      ...mockThread,
      authorAffiliation: null
    };
    render(<ThreadCard thread={threadWithoutAffiliation} />);
    expect(screen.queryByText('工学部')).not.toBeInTheDocument();
  });

  it('shows isMine indicator for own threads', () => {
    const myThread = {
      ...mockThread,
      isMine: true
    };
    render(<ThreadCard thread={myThread} />);
    expect(screen.getByText('自分の投稿')).toBeInTheDocument();
  });
});