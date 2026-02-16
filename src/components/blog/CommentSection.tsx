'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';
import { Send, Trash2, User, LogIn } from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/lib/context/AuthContext';
import { getComments, addComment, deleteComment } from '@/lib/firebase/firestore';
import { formatDate } from '@/lib/utils/dates';
import { Button } from '@/components/ui';
import type { Comment } from '@/lib/types';

interface CommentSectionProps {
  postId: string;
}

export default function CommentSection({ postId }: CommentSectionProps) {
  const { user, isAdmin } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadComments();
  }, [postId]);

  const loadComments = async () => {
    setLoading(true);
    try {
      const data = await getComments(postId);
      setComments(data);
    } catch (err) {
      console.error('Failed to load comments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !content.trim()) return;

    setSubmitting(true);
    try {
      await addComment(postId, {
        content: content.trim(),
        authorId: user.uid,
        authorName: user.displayName || user.email || 'Anonymous',
        authorPhotoUrl: user.photoURL || '',
      });
      setContent('');
      await loadComments();
    } catch (err) {
      console.error('Failed to add comment:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (commentId: string) => {
    if (!confirm('Delete this comment?')) return;
    try {
      await deleteComment(postId, commentId);
      await loadComments();
    } catch (err) {
      console.error('Failed to delete comment:', err);
    }
  };

  return (
    <div className="mt-12 pt-8 border-t border-[#E8E8ED]">
      <h3 className="text-xl font-bold text-[#1D1D1F] mb-6">
        Comments ({comments.length})
      </h3>

      {/* Comment form */}
      {user ? (
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-3">
            <div className="shrink-0">
              {user.photoURL ? (
                <Image
                  src={user.photoURL}
                  alt=""
                  width={36}
                  height={36}
                  className="rounded-full"
                />
              ) : (
                <div className="w-9 h-9 rounded-full bg-[#0071E3] flex items-center justify-center text-white text-sm font-semibold">
                  {(user.displayName || user.email || 'U').charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            <div className="flex-1">
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Write a comment..."
                rows={3}
                className="w-full px-4 py-3 rounded-xl border border-[#D2D2D7] bg-white text-sm text-[#1D1D1F] placeholder:text-[#86868B] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all resize-none"
              />
              <div className="flex justify-end mt-2">
                <Button
                  type="submit"
                  size="sm"
                  disabled={!content.trim() || submitting}
                >
                  <Send size={14} />
                  {submitting ? 'Posting...' : 'Post Comment'}
                </Button>
              </div>
            </div>
          </div>
        </form>
      ) : (
        <div className="mb-8 p-6 rounded-2xl bg-[#F5F5F7] text-center">
          <p className="text-sm text-[#86868B] mb-3">Sign in to leave a comment</p>
          <Link href="/auth/signin">
            <Button size="sm" variant="secondary">
              <LogIn size={14} />
              Sign In
            </Button>
          </Link>
        </div>
      )}

      {/* Comments list */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse flex gap-3">
              <div className="w-9 h-9 rounded-full bg-[#F5F5F7]" />
              <div className="flex-1">
                <div className="h-4 w-24 bg-[#F5F5F7] rounded mb-2" />
                <div className="h-4 w-full bg-[#F5F5F7] rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : comments.length > 0 ? (
        <div className="space-y-6">
          {comments.map((comment) => (
            <div key={comment.id} className="flex gap-3 group">
              <div className="shrink-0">
                {comment.authorPhotoUrl ? (
                  <Image
                    src={comment.authorPhotoUrl}
                    alt=""
                    width={36}
                    height={36}
                    className="rounded-full"
                  />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-[#F5F5F7] flex items-center justify-center text-[#86868B]">
                    <User size={16} />
                  </div>
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-[#1D1D1F]">
                    {comment.authorName}
                  </span>
                  <span className="text-xs text-[#D2D2D7]">
                    {formatDate(comment.createdAt)}
                  </span>
                  {(isAdmin || user?.uid === comment.authorId) && (
                    <button
                      onClick={() => handleDelete(comment.id)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity ml-auto"
                    >
                      <Trash2 size={14} className="text-red-400 hover:text-red-600" />
                    </button>
                  )}
                </div>
                <p className="mt-1 text-sm text-[#424245] leading-relaxed">
                  {comment.content}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-center text-sm text-[#86868B] py-8">
          No comments yet. Be the first to share your thoughts!
        </p>
      )}
    </div>
  );
}
