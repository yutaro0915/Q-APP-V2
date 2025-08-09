/**
 * Thread detail page
 * Server Component for displaying thread details
 */

import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getThread } from '@/lib/actions/getThread';
import { DeleteThreadButton } from '@/components/DeleteThreadButton';
import { ApiError } from '@/lib/api';

interface PageProps {
  params: {
    id: string;
  };
}

// Generate metadata for SEO
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  try {
    const thread = await getThread(params.id);
    return {
      title: `${thread.title} | Kyudai Campus SNS`,
      description: thread.body.slice(0, 160),
    };
  } catch {
    return {
      title: 'スレッドが見つかりません | Kyudai Campus SNS',
    };
  }
}

// Format date to relative time in JST
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}日前`;
  } else if (hours > 0) {
    return `${hours}時間前`;
  } else if (minutes > 0) {
    return `${minutes}分前`;
  } else {
    return '今';
  }
}

export default async function ThreadDetailPage({ params }: PageProps) {
  // Validate thread ID format
  const threadIdRegex = /^thr_[0-9A-HJKMNP-TV-Z]{26}$/;
  if (!threadIdRegex.test(params.id)) {
    notFound();
  }

  let thread;
  try {
    // Fetch thread details without authentication (public view)
    thread = await getThread(params.id);
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 404) {
        notFound();
      }
    }
    // Re-throw other errors
    throw error;
  }

  // Check if thread is deleted
  const isDeleted = thread.title === '[削除済み]' && thread.body === '[削除済み]';

  return (
    <div className="max-w-2xl mx-auto p-4">
      {/* Back link */}
      <Link
        href="/"
        className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
      >
        ← タイムラインに戻る
      </Link>

      {/* Thread content */}
      <article className="bg-white rounded-lg shadow p-6">
        {/* Title */}
        <h1 className="text-2xl font-bold mb-4">
          {thread.title}
        </h1>

        {/* Author and date */}
        <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
          <div className="flex items-center gap-2">
            <span>投稿者:</span>
            {thread.authorProfile && (
              <span className="font-medium">
                {thread.authorProfile.displayName}
              </span>
            )}
            {thread.authorAffiliation && (
              <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                {thread.authorAffiliation.faculty} {thread.authorAffiliation.year}年
              </span>
            )}
          </div>
          <time dateTime={thread.createdAt}>
            {formatRelativeTime(thread.createdAt)}
          </time>
        </div>

        {/* Tags */}
        {thread.tags && thread.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {thread.tags.map((tag) => (
              <span
                key={tag.key}
                className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
              >
                {tag.name}
              </span>
            ))}
          </div>
        )}

        {/* Body */}
        <div className="prose max-w-none mb-6">
          <p className="whitespace-pre-wrap">
            {thread.body}
          </p>
        </div>

        {/* Image */}
        {thread.imageKey && !isDeleted && (
          <div className="mb-6">
            <img
              src={`${process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'}/api/v1/uploads/${thread.imageKey}`}
              alt="Thread attachment"
              className="max-w-full h-auto rounded"
            />
          </div>
        )}

        {/* Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
          <span>👍 {thread.upCount}</span>
          <span>💾 {thread.saveCount}</span>
          <span>🔥 {thread.heat}</span>
        </div>

        {/* Solved status */}
        {thread.solvedCommentId && (
          <div className="bg-green-50 border border-green-200 rounded p-3 mb-4">
            <span className="text-green-800 font-medium">✓ 解決済み</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-4 mt-6 pt-6 border-t">
          {/* Delete button - only show for thread owner */}
          {thread.isMine && !isDeleted && (
            <DeleteThreadButton threadId={thread.id} />
          )}
        </div>

        {/* Comment area placeholder for Phase 2 */}
        <div className="mt-8 pt-8 border-t">
          <p className="text-gray-500 text-center">
            コメント機能は Phase 2 で実装予定
          </p>
        </div>
      </article>
    </div>
  );
}