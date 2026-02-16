import type { Metadata } from 'next';
import { AuthProvider } from '@/lib/context/AuthContext';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'Sehoon Jang — Senior FP&A Manager',
    template: '%s | Sehoon Jang',
  },
  description: '11+ years in FP&A, Project Financing, and Valuation. Currently at Coupang. KAIST MBA.',
  keywords: ['FP&A', 'Financial Planning', 'Portfolio', 'Sehoon Jang', 'Coupang', 'KAIST MBA'],
  authors: [{ name: 'Sehoon Jang' }],
  openGraph: {
    type: 'website',
    locale: 'ko_KR',
    siteName: 'Sehoon Jang Portfolio',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="antialiased">
        <AuthProvider>
          <Navbar />
          <main className="pt-16 min-h-screen">
            {children}
          </main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
