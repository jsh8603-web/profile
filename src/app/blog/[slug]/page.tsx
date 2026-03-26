'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { Badge, Skeleton } from '@/components/ui';
import { getPostBySlug, incrementViewCount } from '@/lib/firebase/firestore';
import type { Post } from '@/lib/types';

const PdfViewer = dynamic(() => import('@/components/blog/PdfViewer'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center py-32">
      <Loader2 className="animate-spin text-[#86868B]" size={32} />
    </div>
  ),
});

const CATEGORY_LABELS: Record<string, { label: string; variant: 'investment' | 'analysis' | 'operations' }> = {
  investment: { label: 'Investment Strategy', variant: 'investment' },
  analysis: { label: 'Financial Analysis', variant: 'analysis' },
  operations: { label: 'Operations & HR', variant: 'operations' },
};

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
        <div className="max-w-5xl mx-auto px-5 sm:px-8">
          <Skeleton className="h-8 w-48 mb-6" />
          <Skeleton className="h-12 w-full mb-4" />
          <Skeleton className="h-[500px] w-full" />
        </div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="section-padding text-center">
        <h1 className="text-2xl font-bold text-[#1D1D1F]">Post not found</h1>
        <p className="mt-2 text-[#86868B]">The publication you&apos;re looking for doesn&apos;t exist.</p>
        <Link href="/blog" className="mt-4 inline-block text-[#0071E3] font-medium hover:underline">
          Back to Publications
        </Link>
      </div>
    );
  }

  const cat = CATEGORY_LABELS[post.category];

  return (
    <div className="section-padding">
      <div className="max-w-5xl mx-auto px-5 sm:px-8">
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
            Back to Publications
          </Link>
        </motion.div>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          {cat && (
            <div className="mb-4">
              <Badge variant={cat.variant}>{cat.label}</Badge>
            </div>
          )}

          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-[#1D1D1F] leading-tight">
            {post.title}
          </h1>
        </motion.div>

        {/* PDF Viewer */}
        {post.attachmentUrl && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="rounded-2xl border border-[#E8E8ED] overflow-hidden bg-white"
          >
            <PdfViewer url={post.attachmentUrl} fileName={post.attachmentName} />
          </motion.div>
        )}
      </div>
    </div>
  );
}
