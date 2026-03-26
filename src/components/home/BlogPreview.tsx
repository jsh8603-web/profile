'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight } from 'lucide-react';
import { ScrollReveal, Badge } from '@/components/ui';
import { getPosts } from '@/lib/firebase/firestore';
import type { Post } from '@/lib/types';

const CATEGORY_LABELS: Record<string, { label: string; variant: 'investment' | 'analysis' | 'operations' }> = {
  investment: { label: 'Investment Strategy', variant: 'investment' },
  analysis: { label: 'Financial Analysis', variant: 'analysis' },
  operations: { label: 'Operations & HR', variant: 'operations' },
};

export default function BlogPreview() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPosts({ pageSize: 3, publishedOnly: true })
      .then(({ posts }) => setPosts(posts))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <section className="section-padding bg-white">
        <div className="max-w-6xl mx-auto px-5 sm:px-8">
          <p className="section-label mb-4">Recent Publications</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card-flat overflow-hidden animate-pulse">
                <div className="h-48 bg-[#F5F5F7]" />
                <div className="p-5">
                  <div className="h-4 w-20 bg-[#F5F5F7] rounded mb-3" />
                  <div className="h-6 w-full bg-[#F5F5F7] rounded" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (posts.length === 0) return null;

  return (
    <section className="section-padding bg-white">
      <div className="max-w-6xl mx-auto px-5 sm:px-8">
        <ScrollReveal>
          <div className="flex items-end justify-between mb-8">
            <div>
              <p className="section-label mb-4">Recent Publications</p>
              <h2 className="text-3xl sm:text-4xl font-bold text-[#1D1D1F]">
                Slides &amp; Reports
              </h2>
            </div>
            <Link
              href="/blog"
              className="hidden sm:flex items-center gap-1 text-sm font-medium text-[#0071E3] hover:underline"
            >
              View all <ArrowRight size={16} />
            </Link>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {posts.map((post, i) => {
            const cat = CATEGORY_LABELS[post.category];
            return (
              <ScrollReveal key={post.id} delay={i * 0.1}>
                <Link href={`/blog/${post.slug}`} className="card block h-full group overflow-hidden">
                  {post.coverImageUrl && (
                    <div className="relative h-48 overflow-hidden bg-[#F5F5F7]">
                      <Image
                        src={post.coverImageUrl}
                        alt={post.title}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    </div>
                  )}
                  <div className="p-5">
                    {cat && (
                      <Badge variant={cat.variant}>{cat.label}</Badge>
                    )}
                    <h3 className="mt-3 text-lg font-semibold text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors line-clamp-2">
                      {post.title}
                    </h3>
                  </div>
                </Link>
              </ScrollReveal>
            );
          })}
        </div>

        <Link
          href="/blog"
          className="sm:hidden flex items-center justify-center gap-1 mt-6 text-sm font-medium text-[#0071E3]"
        >
          View all publications <ArrowRight size={16} />
        </Link>
      </div>
    </section>
  );
}
