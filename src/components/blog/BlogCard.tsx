'use client';

import Link from 'next/link';
import Image from 'next/image';
import { MessageCircle, Eye, Clock } from 'lucide-react';
import { Badge } from '@/components/ui';
import { formatDate } from '@/lib/utils/dates';
import type { Post } from '@/lib/types';

interface BlogCardProps {
  post: Post;
}

export default function BlogCard({ post }: BlogCardProps) {
  return (
    <Link href={`/blog/${post.slug}`} className="card group block overflow-hidden">
      {post.coverImageUrl && (
        <div className="relative h-48 overflow-hidden">
          <Image
            src={post.coverImageUrl}
            alt={post.title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-500"
          />
        </div>
      )}

      <div className="p-6">
        <div className="flex items-center gap-2 mb-3">
          <Badge variant={post.category === 'finance' ? 'finance' : 'economy'}>
            {post.category === 'finance' ? 'Finance' : 'Economy'}
          </Badge>
          {post.tags.slice(0, 2).map((tag) => (
            <Badge key={tag} variant="outline">{tag}</Badge>
          ))}
        </div>

        <h3 className="text-lg font-semibold text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors line-clamp-2">
          {post.title}
        </h3>

        <p className="mt-2 text-sm text-[#86868B] line-clamp-2 leading-relaxed">
          {post.excerpt}
        </p>

        <div className="mt-4 flex items-center gap-4 text-xs text-[#D2D2D7]">
          <span className="flex items-center gap-1">
            <Clock size={12} />
            {formatDate(post.createdAt)}
          </span>
          <span className="flex items-center gap-1">
            <Eye size={12} />
            {post.viewCount || 0}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircle size={12} />
            {post.commentCount || 0}
          </span>
        </div>
      </div>
    </Link>
  );
}
