'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, LogIn, LogOut, Shield } from 'lucide-react';
import { useAuth } from '@/lib/context/AuthContext';
import { signOut } from '@/lib/firebase/auth';

const NAV_ITEMS = [
  { href: '/', label: 'Home' },
  { href: '/resume', label: 'Resume' },
  { href: '/blog', label: 'Blog' },
  { href: '/contact', label: 'Contact' },
];

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  const { user, isAdmin } = useAuth();

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-[#E8E8ED]/60">
        <div className="max-w-6xl mx-auto px-5 sm:px-8 flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-[#1D1D1F] tracking-tight">
              SJ
            </span>
            <span className="hidden sm:inline text-sm text-[#86868B] font-medium">
              Sehoon Jang
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                  isActive(item.href)
                    ? 'bg-[#1D1D1F] text-white'
                    : 'text-[#424245] hover:text-[#1D1D1F] hover:bg-[#F5F5F7]'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>

          {/* Right side: Auth + Admin */}
          <div className="flex items-center gap-2">
            {isAdmin && (
              <Link
                href="/admin"
                className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-[#0071E3]/10 text-[#0071E3] hover:bg-[#0071E3]/20 transition-colors"
              >
                <Shield size={14} />
                Admin
              </Link>
            )}

            {user ? (
              <button
                onClick={() => signOut()}
                className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-[#86868B] hover:text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors"
              >
                <LogOut size={14} />
                Sign Out
              </button>
            ) : (
              <Link
                href="/auth/signin"
                className="hidden md:flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium bg-[#1D1D1F] text-white hover:bg-[#333336] transition-colors"
              >
                <LogIn size={14} />
                Sign In
              </Link>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-xl hover:bg-[#F5F5F7] transition-colors"
            >
              {mobileOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="fixed top-16 left-0 right-0 z-40 glass border-b border-[#E8E8ED] md:hidden"
          >
            <div className="px-5 py-4 flex flex-col gap-1">
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMobileOpen(false)}
                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive(item.href)
                      ? 'bg-[#1D1D1F] text-white'
                      : 'text-[#424245] hover:bg-[#F5F5F7]'
                  }`}
                >
                  {item.label}
                </Link>
              ))}

              <div className="h-px bg-[#E8E8ED] my-2" />

              {isAdmin && (
                <Link
                  href="/admin"
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium text-[#0071E3] hover:bg-[#0071E3]/10 transition-colors"
                >
                  <Shield size={16} />
                  Admin Dashboard
                </Link>
              )}

              {user ? (
                <button
                  onClick={() => { signOut(); setMobileOpen(false); }}
                  className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium text-[#86868B] hover:bg-[#F5F5F7] transition-colors text-left"
                >
                  <LogOut size={16} />
                  Sign Out
                </button>
              ) : (
                <Link
                  href="/auth/signin"
                  onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium text-[#1D1D1F] bg-[#F5F5F7] hover:bg-[#E8E8ED] transition-colors"
                >
                  <LogIn size={16} />
                  Sign In
                </Link>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
