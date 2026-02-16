'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { motion } from 'framer-motion';
import { ArrowLeft, Clock, Eye, MessageCircle, Tag, FileDown } from 'lucide-react';
import { Badge, Skeleton } from '@/components/ui';
import CommentSection from '@/components/blog/CommentSection';
import { getPostBySlug, incrementViewCount } from '@/lib/firebase/firestore';
import { formatDate } from '@/lib/utils/dates';
import type { Post } from '@/lib/types';

export default function BlogPostPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;

    getPostBySlug(slug)
      .then((data) => {
        setPost(data);
        if (data) {
          incrementViewCount(data.id).catch(() => {});
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="section-padding">
        <div className="max-w-3xl mx-auto px-5 sm:px-8">
          <Skeleton className="h-8 w-48 mb-6" />
          <Skeleton className="h-12 w-full mb-4" />
          <Skeleton className="h-6 w-2/3 mb-8" />
          <Skeleton className="h-64 w-full mb-4" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="section-padding text-center">
        <h1 className="text-2xl font-bold text-[#1D1D1F]">Post not found</h1>
        <p className="mt-2 text-[#86868B]">The post you&apos;re looking for doesn&apos;t exist.</p>
        <Link href="/blog" className="mt-4 inline-block text-[#0071E3] font-medium hover:underline">
          Back to Blog
        </Link>
      </div>
    );
  }

  return (
    <div className="section-padding">
      <article className="max-w-3xl mx-auto px-5 sm:px-8">
        {/* Back link */}
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Link
            href="/blog"
            className="inline-flex items-center gap-1.5 text-sm text-[#86868B] hover:text-[#0071E3] transition-colors mb-8"
          >
            <ArrowLeft size={16} />
            Back to Blog
          </Link>
        </motion.div>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex items-center gap-2 mb-4">
            <Badge variant={post.category === 'finance' ? 'finance' : 'economy'}>
              {post.category === 'finance' ? 'Finance' : 'Economy'}
            </Badge>
          </div>

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-[#1D1D1F] leading-tight">
            {post.title}
          </h1>

          {post.excerpt && (
            <p className="mt-4 text-lg text-[#86868B] leading-relaxed">
              {post.excerpt}
            </p>
          )}

          <div className="flex flex-wrap items-center gap-4 mt-6 pb-8 border-b border-[#E8E8ED]">
            <span className="flex items-center gap-1.5 text-sm text-[#86868B]">
              <Clock size={14} />
              {formatDate(post.publishedAt || post.createdAt)}
            </span>
            <span className="flex items-center gap-1.5 text-sm text-[#86868B]">
              <Eye size={14} />
              {post.viewCount || 0} views
            </span>
            <span className="flex items-center gap-1.5 text-sm text-[#86868B]">
              <MessageCircle size={14} />
              {post.commentCount || 0} comments
            </span>
          </div>

          {post.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-4">
              {post.tags.map((tag) => (
                <span key={tag} className="flex items-center gap-1 text-xs text-[#86868B] bg-[#F5F5F7] px-2.5 py-1 rounded-full">
                  <Tag size={10} />
                  {tag}
                </span>
              ))}
            </div>
          )}
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-10"
        >
          <div className="prose prose-lg max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
            >
              {post.content}
            </ReactMarkdown>
          </div>
        </motion.div>

        {/* PDF Attachment */}
        {post.attachmentUrl && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-10 p-6 rounded-2xl bg-[#F5F5F7] border border-[#E8E8ED]"
          >
            <a
              href={post.attachmentUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 text-[#0071E3] hover:text-[#0077ED] transition-colors"
            >
              <FileDown size={20} />
              <div>
                <span className="font-medium text-sm">
                  {post.attachmentName || 'Download PDF'}
                </span>
                <span className="block text-xs text-[#86868B] mt-0.5">
                  PDF 파일 다운로드
                </span>
              </div>
            </a>
          </motion.div>
        )}

        {/* Comments */}
        <CommentSection postId={post.id} />
      </article>
    </div>
  );
}
