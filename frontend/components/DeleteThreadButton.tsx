'use client';

/**
 * Delete thread button component
 * Client component for handling thread deletion with confirmation
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { deleteThread } from '@/lib/actions/deleteThread';
import { DeleteConfirmDialog } from '@/components/DeleteConfirmDialog';
import { ApiError } from '@/lib/api';

interface DeleteThreadButtonProps {
  threadId: string;
}

export function DeleteThreadButton({ threadId }: DeleteThreadButtonProps) {
  const router = useRouter();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    setError(null);

    try {
      await deleteThread(threadId);
      // Close dialog first
      setIsDialogOpen(false);
      // Redirect to timeline after successful deletion
      router.push('/');
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 403) {
          throw new Error('このスレッドを削除する権限がありません');
        } else if (error.status === 404) {
          throw new Error('スレッドが見つかりません');
        } else if (error.status === 401) {
          throw new Error('ログインが必要です');
        } else {
          throw new Error(error.message || 'スレッドの削除に失敗しました');
        }
      } else if (error instanceof Error) {
        throw error;
      } else {
        throw new Error('スレッドの削除に失敗しました');
      }
    }
  };

  return (
    <>
      <button
        onClick={() => setIsDialogOpen(true)}
        className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        aria-label="スレッドを削除"
      >
        削除
      </button>
      
      <DeleteConfirmDialog
        isOpen={isDialogOpen}
        title="スレッドの削除"
        message="このスレッドを削除してもよろしいですか？この操作は取り消せません。"
        onConfirm={handleDelete}
        onCancel={() => setIsDialogOpen(false)}
      />
      
      {error && !isDialogOpen && (
        <p className="mt-2 text-red-600 text-sm">{error}</p>
      )}
    </>
  );
}