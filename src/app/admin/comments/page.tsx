'use client';

import { useState, useEffect } from 'react';
import { Trash2, MessageCircle } from 'lucide-react';
import { collection, getDocs, query, orderBy } from 'firebase/firestore';
import { requireDb } from '@/lib/firebase/config';
import { deleteComment } from '@/lib/firebase/firestore';
import { formatDate } from '@/lib/utils/dates';
import type { Comment } from '@/lib/types';

interface CommentWithPost extends Comment {
  postTitle: string;
  postId: string;
}

export default function AdminCommentsPage() {
  const [comments, setComments] = useState<CommentWithPost[]>([]);
  const [loading, setLoading] = useState(true);

  const loadComments = async () => {
    setLoading(true);
    try {
      const db = requireDb();
      const postsSnap = await getDocs(collection(db, 'posts'));
      const allComments: CommentWithPost[] = [];

      for (const postDoc of postsSnap.docs) {
        const postData = postDoc.data();
        const commentsSnap = await getDocs(
          query(collection(requireDb(), 'posts', postDoc.id, 'comments'), orderBy('createdAt', 'desc'))
        );
        commentsSnap.docs.forEach(cDoc => {
          allComments.push({
            id: cDoc.id,
            ...cDoc.data(),
            postTitle: postData.title,
            postId: postDoc.id,
          } as CommentWithPost);
        });
      }

      allComments.sort((a, b) => {
        const aTime = a.createdAt?.toMillis?.() || 0;
        const bTime = b.createdAt?.toMillis?.() || 0;
        return bTime - aTime;
      });

      setComments(allComments);
    } catch (err) {
      console.error('Failed to load comments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadComments(); }, []);

  const handleDelete = async (postId: string, commentId: string) => {
    if (!confirm('Delete this comment?')) return;
    try {
      await deleteComment(postId, commentId);
      await loadComments();
    } catch (err) {
      console.error('Failed to delete comment:', err);
    }
  };

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold text-[#1D1D1F] mb-1">Comments</h1>
      <p className="text-sm text-[#86868B] mb-8">Manage all comments across posts</p>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="card-flat p-5 animate-pulse">
              <div className="h-4 w-32 bg-[#F5F5F7] rounded mb-2" />
              <div className="h-4 w-full bg-[#F5F5F7] rounded" />
            </div>
          ))}
        </div>
      ) : comments.length > 0 ? (
        <div className="space-y-3">
          {comments.map((comment) => (
            <div key={comment.id} className="card-flat p-5 flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-[#1D1D1F]">{comment.authorName}</span>
                  <span className="text-xs text-[#D2D2D7]">on</span>
                  <span className="text-xs font-medium text-[#0071E3] truncate">{comment.postTitle}</span>
                </div>
                <p className="text-sm text-[#424245] mb-1">{comment.content}</p>
                <p className="text-xs text-[#86868B]">{formatDate(comment.createdAt)}</p>
              </div>
              <button
                onClick={() => handleDelete(comment.postId, comment.id)}
                className="p-2 rounded-lg hover:bg-red-50 transition-colors shrink-0"
              >
                <Trash2 size={16} className="text-red-400" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 card-flat">
          <MessageCircle size={32} className="mx-auto text-[#D2D2D7] mb-3" />
          <p className="text-[#86868B]">No comments yet</p>
        </div>
      )}
    </div>
  );
}
