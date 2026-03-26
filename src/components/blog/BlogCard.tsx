'use client';

import Link from 'next/link';
import Image from 'next/image';
import { Badge } from '@/components/ui';
import type { Post } from '@/lib/types';

const CATEGORY_LABELS: Record<string, { label: string; variant: 'investment' | 'analysis' | 'operations' }> = {
  investment: { label: 'Investment Strategy', variant: 'investment' },
  analysis: { label: 'Financial Analysis', variant: 'analysis' },
  operations: { label: 'Operations & HR', variant: 'operations' },
};

interface BlogCardProps {
  post: Post;
}

export default function BlogCard({ post }: BlogCardProps) {
  const cat = CATEGORY_LABELS[post.category];

  return (
    <Link href={`/blog/${post.slug}`} className="card group block overflow-hidden">
      {post.coverImageUrl && (
        <div className="relative h-64 sm:h-72 overflow-hidden bg-[#F5F5F7]">
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
  );
}
