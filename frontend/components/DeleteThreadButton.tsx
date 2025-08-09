'use client';

/**
 * Delete thread button component
 * Client component for handling thread deletion with confirmation
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { deleteThread } from '@/lib/actions/deleteThread';
import { ApiError } from '@/lib/api';

interface DeleteThreadButtonProps {
  threadId: string;
}

export function DeleteThreadButton({ threadId }: DeleteThreadButtonProps) {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    // Simple confirmation for now (P1-FRONT-UX-DeleteConfirm will enhance this)
    if (!confirm('このスレッドを削除してもよろしいですか？')) {
      return;
    }

    setIsDeleting(true);
    setError(null);

    try {
      await deleteThread(threadId);
      // Redirect to timeline after successful deletion
      router.push('/');
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 403) {
          setError('このスレッドを削除する権限がありません');
        } else if (error.status === 404) {
          setError('スレッドが見つかりません');
        } else if (error.status === 401) {
          setError('ログインが必要です');
        } else {
          setError(error.message || 'スレッドの削除に失敗しました');
        }
      } else if (error instanceof Error) {
        setError(error.message);
      } else {
        setError('スレッドの削除に失敗しました');
      }
      setIsDeleting(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleDelete}
        disabled={isDeleting}
        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        aria-label="スレッドを削除"
      >
        {isDeleting ? '削除中...' : '削除'}
      </button>
      {error && (
        <p className="mt-2 text-red-600 text-sm">{error}</p>
      )}
    </div>
  );
}