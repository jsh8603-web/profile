'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, FileText, MessageCircle, User, ArrowLeft, Sparkles
} from 'lucide-react';

const MENU_ITEMS = [
  { href: '/admin', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/admin/posts', label: 'Posts', icon: FileText },
  { href: '/admin/comments', label: 'Comments', icon: MessageCircle },
  { href: '/admin/skills', label: 'Skills', icon: Sparkles },
  { href: '/admin/profile', label: 'Profile', icon: User },
];

export default function AdminSidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === '/admin') return pathname === '/admin';
    return pathname.startsWith(href);
  };

  return (
    <aside className="w-64 shrink-0 border-r border-[#E8E8ED] bg-white min-h-[calc(100vh-4rem)] p-4 hidden lg:block">
      <div className="mb-6">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm text-[#86868B] hover:text-[#0071E3] transition-colors"
        >
          <ArrowLeft size={16} />
          Back to site
        </Link>
      </div>

      <div className="mb-4">
        <span className="text-xs font-semibold tracking-wider uppercase text-[#86868B]">
          Admin
        </span>
      </div>

      <nav className="space-y-1">
        {MENU_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`admin-sidebar-link ${isActive(item.href) ? 'active' : 'text-[#424245]'}`}
          >
            <item.icon size={18} />
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
