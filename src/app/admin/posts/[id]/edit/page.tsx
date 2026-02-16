'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import PostForm from '@/components/admin/PostForm';
import { getPostById } from '@/lib/firebase/firestore';
import { Skeleton } from '@/components/ui';
import type { Post } from '@/lib/types';

export default function EditPostPage() {
  const params = useParams();
  const id = params.id as string;
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPostById(id)
      .then(setPost)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-4xl space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!post) {
    return <p className="text-[#86868B]">Post not found.</p>;
  }

  return <PostForm post={post} mode="edit" />;
}
