/**
 * Timeline (New) page
 * Server Component for displaying thread list
 */

import Link from 'next/link';
import { ThreadCard } from '@/components/ThreadCard';
import { getThreads } from '@/lib/actions/getThreads';
import { ApiError } from '@/lib/api';

// Convert API thread to ThreadCard props
function convertToThreadCardProps(thread: any) {
  // Convert tags to ThreadCard format
  const tags = thread.tags?.map((tag: any) => ({
    key: tag.key || '種別',
    value: tag.name || tag.value || '',
  })) || [];

  // Extract first 120 characters of body as excerpt
  const excerpt = thread.body ? thread.body.substring(0, 120) : '';

  return {
    id: thread.id,
    title: thread.title,
    excerpt,
    tags,
    heat: thread.heat || 0,
    replies: 0, // TODO: Get actual reply count from API in Phase 2
    saves: thread.saveCount || 0,
    createdAt: thread.createdAt,
    lastReplyAt: thread.lastActivityAt || null,
    hasImage: !!thread.imageKey,
    imageThumbUrl: thread.imageKey 
      ? `${process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'}/api/v1/uploads/${thread.imageKey}`
      : null,
    solved: !!thread.solvedCommentId,
    authorAffiliation: thread.authorAffiliation || null,
    isMine: thread.isMine || false,
  };
}

export default async function HomePage() {
  let threads = [];
  let error = null;

  try {
    // Fetch threads without authentication (public view)
    const response = await getThreads('new');
    threads = response.threads || [];
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 500) {
        error = 'サーバーエラーが発生しました。しばらくしてからお試しください。';
      } else {
        error = err.message || 'スレッドの取得に失敗しました。';
      }
    } else {
      error = 'ネットワークエラーが発生しました。接続を確認してください。';
    }
    console.error('Failed to fetch threads:', err);
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            Kyudai Campus SNS
          </h1>
          <p className="text-gray-600">
            九州大学の学生・教職員向けQ&Aプラットフォーム
          </p>
        </header>

        {/* New thread button */}
        <div className="mb-6 flex justify-end">
          <Link
            href="/thread/new"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            新規投稿
          </Link>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Thread list */}
        {!error && threads.length === 0 ? (
          <div className="bg-gray-50 rounded-lg p-12 text-center">
            <svg
              className="w-16 h-16 mx-auto mb-4 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
            <h2 className="text-xl font-semibold text-gray-700 mb-2">
              まだスレッドがありません
            </h2>
            <p className="text-gray-600 mb-4">
              最初のスレッドを投稿してみましょう！
            </p>
            <Link
              href="/thread/new"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              新規投稿する
            </Link>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {threads.map((thread) => (
                <ThreadCard
                  key={thread.id}
                  thread={convertToThreadCardProps(thread)}
                />
              ))}
            </div>

            {/* Load more button (placeholder for Phase 2) */}
            {threads.length >= 20 && (
              <div className="mt-8 text-center">
                <button
                  disabled
                  className="px-6 py-2 bg-gray-100 text-gray-500 rounded-lg cursor-not-allowed"
                >
                  もっと見る（Phase 2で実装予定）
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}