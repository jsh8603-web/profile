'use client';

import { Suspense, useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { ScrollReveal, Skeleton } from '@/components/ui';
import BlogCard from '@/components/blog/BlogCard';
import CategoryFilter from '@/components/blog/CategoryFilter';
import { getPosts } from '@/lib/firebase/firestore';
import type { Post } from '@/lib/types';
import type { QueryDocumentSnapshot, DocumentData } from 'firebase/firestore';

function BlogContent() {
  const searchParams = useSearchParams();
  const initialCategory = searchParams.get('category') || '';

  const [posts, setPosts] = useState<Post[]>([]);
  const [category, setCategory] = useState(initialCategory);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const lastDocRef = useRef<QueryDocumentSnapshot<DocumentData> | null>(null);
  const [hasMore, setHasMore] = useState(false);

  const loadPosts = async (cat: string, append = false) => {
    if (append) setLoadingMore(true);
    else setLoading(true);

    try {
      const result = await getPosts({
        category: cat || undefined,
        publishedOnly: true,
        pageSize: 9,
        lastDoc: append ? lastDocRef.current || undefined : undefined,
      });

      setPosts(prev => append ? [...prev, ...result.posts] : result.posts);
      lastDocRef.current = result.lastVisible;
      setHasMore(result.hasMore);
    } catch (err) {
      console.error('Failed to load posts:', err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  useEffect(() => {
    loadPosts(category);
  }, [category]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCategoryChange = (cat: string) => {
    setCategory(cat);
    lastDocRef.current = null;
  };

  return (
    <div className="section-padding">
      <div className="max-w-6xl mx-auto px-5 sm:px-8">
        <ScrollReveal>
          <p className="section-label mb-4">Blog</p>
          <h1 className="text-4xl sm:text-5xl font-bold text-[#1D1D1F]">
            Insights &amp; Analysis
          </h1>
          <p className="mt-4 text-lg text-[#86868B] max-w-xl">
            Thoughts on finance, economics, and the intersection of data and decision-making.
          </p>
        </ScrollReveal>

        <div className="mt-8 mb-10">
          <CategoryFilter selected={category} onChange={handleCategoryChange} />
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="card-flat p-6">
                <Skeleton className="h-4 w-20 mb-4" />
                <Skeleton className="h-6 w-full mb-2" />
                <Skeleton className="h-6 w-3/4 mb-4" />
                <Skeleton className="h-4 w-full mb-2" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            ))}
          </div>
        ) : posts.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {posts.map((post, i) => (
                <motion.div
                  key={post.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: i * 0.05 }}
                >
                  <BlogCard post={post} />
                </motion.div>
              ))}
            </div>

            {hasMore && (
              <div className="mt-10 text-center">
                <button
                  onClick={() => loadPosts(category, true)}
                  disabled={loadingMore}
                  className="px-8 py-3 rounded-full text-sm font-medium bg-[#F5F5F7] text-[#1D1D1F] hover:bg-[#E8E8ED] transition-colors disabled:opacity-50"
                >
                  {loadingMore ? 'Loading...' : 'Load More'}
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-20">
            <p className="text-lg text-[#86868B]">No posts yet.</p>
            <p className="text-sm text-[#D2D2D7] mt-2">Check back soon for new content!</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function BlogPage() {
  return (
    <Suspense fallback={
      <div className="section-padding">
        <div className="max-w-6xl mx-auto px-5 sm:px-8">
          <Skeleton className="h-8 w-32 mb-4" />
          <Skeleton className="h-12 w-64 mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card-flat p-6">
                <Skeleton className="h-6 w-full mb-2" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ))}
          </div>
        </div>
      </div>
    }>
      <BlogContent />
    </Suspense>
  );
}
