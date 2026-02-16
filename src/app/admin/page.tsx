'use client';

import { useEffect, useState } from 'react';
import { FileText, Eye, MessageCircle, TrendingUp } from 'lucide-react';
import { getAdminStats } from '@/lib/firebase/firestore';

interface Stats {
  totalPosts: number;
  publishedPosts: number;
  draftPosts: number;
  totalComments: number;
  totalViews: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const cards = stats
    ? [
        { label: 'Total Posts', value: stats.totalPosts, icon: FileText, color: '#0071E3' },
        { label: 'Published', value: stats.publishedPosts, icon: TrendingUp, color: '#34C759' },
        { label: 'Total Views', value: stats.totalViews, icon: Eye, color: '#FF9500' },
        { label: 'Comments', value: stats.totalComments, icon: MessageCircle, color: '#AF52DE' },
      ]
    : [];

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-bold text-[#1D1D1F] mb-1">Dashboard</h1>
      <p className="text-sm text-[#86868B] mb-8">Welcome back. Here&apos;s an overview of your site.</p>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card-flat p-6 animate-pulse">
              <div className="h-4 w-20 bg-[#F5F5F7] rounded mb-4" />
              <div className="h-8 w-16 bg-[#F5F5F7] rounded" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map((card) => (
            <div key={card.label} className="card-flat p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-[#86868B]">{card.label}</span>
                <card.icon size={18} style={{ color: card.color }} />
              </div>
              <div className="text-3xl font-bold text-[#1D1D1F]">
                {card.value.toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {stats && (
        <div className="mt-8 card-flat p-6">
          <h2 className="text-lg font-semibold text-[#1D1D1F] mb-4">Quick Summary</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-[#F5F5F7]">
              <span className="text-sm text-[#424245]">Draft posts</span>
              <span className="text-sm font-medium text-[#1D1D1F]">{stats.draftPosts}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-[#F5F5F7]">
              <span className="text-sm text-[#424245]">Average views per post</span>
              <span className="text-sm font-medium text-[#1D1D1F]">
                {stats.totalPosts > 0 ? Math.round(stats.totalViews / stats.totalPosts) : 0}
              </span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-[#424245]">Average comments per post</span>
              <span className="text-sm font-medium text-[#1D1D1F]">
                {stats.totalPosts > 0 ? (stats.totalComments / stats.totalPosts).toFixed(1) : '0'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
