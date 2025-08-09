'use client';

import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { ja } from 'date-fns/locale';
import { MessageCircle, Bookmark } from 'lucide-react';

export interface ThreadTag {
  key: string;
  value: string;
}

export interface AuthorAffiliation {
  faculty: string | null;
  year: number | null;
}

export interface ThreadCardProps {
  thread: {
    id: string;
    title: string;
    excerpt: string;
    tags: ThreadTag[];
    heat: number;
    replies: number;
    saves: number;
    createdAt: string;
    lastReplyAt: string | null;
    hasImage: boolean;
    imageThumbUrl: string | null;
    solved: boolean;
    authorAffiliation: AuthorAffiliation | null;
    isMine?: boolean;
  };
}

function getThreadType(tags: ThreadTag[]): string {
  const typeTag = tags.find(tag => tag.key === '種別');
  return typeTag?.value || 'chat';
}

function getThreadColorClass(type: string): string {
  switch (type) {
    case 'question':
      return 'border-blue-500 hover:border-blue-600';
    case 'notice':
      return 'border-orange-500 hover:border-orange-600';
    case 'recruit':
      return 'border-green-500 hover:border-green-600';
    case 'chat':
    default:
      return 'border-gray-500 hover:border-gray-600';
  }
}

function getThreadTypeLabel(type: string): string {
  switch (type) {
    case 'question':
      return '質問';
    case 'notice':
      return '告知';
    case 'recruit':
      return '募集';
    case 'chat':
    default:
      return '雑談';
  }
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

  if (diffInHours < 24) {
    return formatDistanceToNow(date, { addSuffix: true, locale: ja });
  }

  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `${year}年${month}月${day}日`;
}

function truncateExcerpt(text: string, maxLength: number = 120): string {
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength) + '…';
}

export function ThreadCard({ thread }: ThreadCardProps) {
  const threadType = getThreadType(thread.tags);
  const colorClass = getThreadColorClass(threadType);
  const truncatedExcerpt = truncateExcerpt(thread.excerpt);

  return (
    <Link 
      href={`/threads/${thread.id}`}
      aria-label={`スレッド: ${thread.title}`}
    >
      <article
        data-testid="thread-card"
        className={`block p-4 mb-3 bg-white rounded-lg border-l-4 ${colorClass} shadow-sm hover:shadow-md transition-shadow cursor-pointer`}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${
                threadType === 'question' ? 'bg-blue-100 text-blue-800' :
                threadType === 'notice' ? 'bg-orange-100 text-orange-800' :
                threadType === 'recruit' ? 'bg-green-100 text-green-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {getThreadTypeLabel(threadType)}
              </span>
              
              {thread.solved && threadType === 'question' && (
                <span className="inline-block px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                  解決済み
                </span>
              )}

              {thread.isMine && (
                <span className="inline-block px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800 rounded-full">
                  自分の投稿
                </span>
              )}
            </div>

            <h3 className="text-lg font-semibold text-gray-900 mb-1 line-clamp-2">
              {thread.title}
            </h3>
          </div>
        </div>

        {/* Excerpt */}
        <p data-testid="thread-excerpt" className="text-gray-600 text-sm mb-3 line-clamp-2">
          {truncatedExcerpt}
        </p>

        {/* Tags */}
        {thread.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {thread.tags.map((tag, index) => {
              if (tag.key === '種別') return null;
              return (
                <span
                  key={index}
                  className="inline-block px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                >
                  {tag.value}
                </span>
              );
            })}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <MessageCircle className="w-3 h-3" />
              <span>{thread.replies}</span>
            </span>
            <span className="flex items-center gap-1">
              <Bookmark className="w-3 h-3" />
              <span>{thread.saves}</span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            {thread.authorAffiliation && (
              <span className="text-gray-600">
                {thread.authorAffiliation.faculty} {thread.authorAffiliation.year}年
              </span>
            )}
            
            <span>
              {formatTime(thread.createdAt)}
            </span>
            
            {thread.lastReplyAt && (
              <span className="text-gray-400">
                最終返信: {formatTime(thread.lastReplyAt)}
              </span>
            )}
          </div>
        </div>
      </article>
    </Link>
  );
}