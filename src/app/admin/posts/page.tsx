'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Edit, Trash2, Eye, EyeOff } from 'lucide-react';
import { getPosts, deletePost, updatePost } from '@/lib/firebase/firestore';
import { formatDate } from '@/lib/utils/dates';
import { Badge, Button } from '@/components/ui';
import type { Post } from '@/lib/types';

export default function AdminPostsPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  const loadPosts = async () => {
    setLoading(true);
    try {
      const result = await getPosts({ publishedOnly: false, pageSize: 100 });
      setPosts(result.posts);
    } catch (err) {
      console.error('Failed to load posts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadPosts(); }, []);

  const handleTogglePublish = async (post: Post) => {
    try {
      await updatePost(post.id, { published: !post.published });
      await loadPosts();
    } catch (err) {
      console.error('Failed to toggle publish:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this post?')) return;
    try {
      await deletePost(id);
      await loadPosts();
    } catch (err) {
      console.error('Failed to delete post:', err);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">Posts</h1>
          <p className="text-sm text-[#86868B] mt-1">Manage your blog posts</p>
        </div>
        <Link href="/admin/posts/new">
          <Button>
            <Plus size={16} />
            New Post
          </Button>
        </Link>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card-flat p-5 animate-pulse">
              <div className="h-5 w-48 bg-[#F5F5F7] rounded mb-2" />
              <div className="h-4 w-32 bg-[#F5F5F7] rounded" />
            </div>
          ))}
        </div>
      ) : posts.length > 0 ? (
        <div className="space-y-3">
          {posts.map((post) => (
            <div key={post.id} className="card-flat p-5 flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-[#1D1D1F] truncate">
                    {post.title}
                  </h3>
                  <Badge variant={post.published ? 'finance' : 'outline'}>
                    {post.published ? 'Published' : 'Draft'}
                  </Badge>
                  <Badge variant={post.category === 'finance' ? 'finance' : 'economy'}>
                    {post.category}
                  </Badge>
                </div>
                <p className="text-xs text-[#86868B]">
                  {formatDate(post.createdAt)} · {post.viewCount || 0} views · {post.commentCount || 0} comments
                </p>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  onClick={() => handleTogglePublish(post)}
                  className="p-2 rounded-lg hover:bg-[#F5F5F7] transition-colors"
                  title={post.published ? 'Unpublish' : 'Publish'}
                >
                  {post.published ? (
                    <EyeOff size={16} className="text-[#86868B]" />
                  ) : (
                    <Eye size={16} className="text-[#0071E3]" />
                  )}
                </button>
                <Link
                  href={`/admin/posts/${post.id}/edit`}
                  className="p-2 rounded-lg hover:bg-[#F5F5F7] transition-colors"
                >
                  <Edit size={16} className="text-[#86868B]" />
                </Link>
                <button
                  onClick={() => handleDelete(post.id)}
                  className="p-2 rounded-lg hover:bg-red-50 transition-colors"
                >
                  <Trash2 size={16} className="text-red-400" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 card-flat">
          <p className="text-[#86868B] mb-4">No posts yet</p>
          <Link href="/admin/posts/new">
            <Button>
              <Plus size={16} />
              Create Your First Post
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
