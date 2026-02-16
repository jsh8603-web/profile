import Link from 'next/link';
import { Mail, Phone, MapPin } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-[#E8E8ED] bg-white">
      <div className="max-w-6xl mx-auto px-5 sm:px-8 py-12 sm:py-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="lg:col-span-1">
            <span className="text-xl font-bold text-[#1D1D1F] tracking-tight">
              Sehoon Jang
            </span>
            <p className="mt-2 text-sm text-[#86868B] leading-relaxed">
              Senior FP&A Manager with 11+ years of experience in financial planning and analysis.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-3">Pages</h4>
            <div className="flex flex-col gap-2">
              {[
                { href: '/', label: 'Home' },
                { href: '/resume', label: 'Resume' },
                { href: '/blog', label: 'Blog' },
                { href: '/contact', label: 'Contact' },
              ].map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm text-[#86868B] hover:text-[#0071E3] transition-colors"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Blog Categories */}
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-3">Blog</h4>
            <div className="flex flex-col gap-2">
              <Link href="/blog?category=finance" className="text-sm text-[#86868B] hover:text-[#0071E3] transition-colors">
                Finance
              </Link>
              <Link href="/blog?category=economy" className="text-sm text-[#86868B] hover:text-[#0071E3] transition-colors">
                Economy
              </Link>
            </div>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-sm font-semibold text-[#1D1D1F] mb-3">Contact</h4>
            <div className="flex flex-col gap-2.5">
              <a href="mailto:jsh8603@gmail.com" className="flex items-center gap-2 text-sm text-[#86868B] hover:text-[#0071E3] transition-colors">
                <Mail size={14} />
                jsh8603@gmail.com
              </a>
              <a href="tel:+821027028602" className="flex items-center gap-2 text-sm text-[#86868B] hover:text-[#0071E3] transition-colors">
                <Phone size={14} />
                +82 010-2702-8602
              </a>
              <span className="flex items-center gap-2 text-sm text-[#86868B]">
                <MapPin size={14} />
                Seoul, Korea
              </span>
            </div>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-[#E8E8ED] flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-[#86868B]">
            &copy; {new Date().getFullYear()} Sehoon Jang. All rights reserved.
          </p>
          <p className="text-xs text-[#D2D2D7]">
            Built with Next.js & Firebase
          </p>
        </div>
      </div>
    </footer>
  );
}
