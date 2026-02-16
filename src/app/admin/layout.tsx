'use client';

import AuthGuard from '@/components/auth/AuthGuard';
import AdminSidebar from '@/components/admin/AdminSidebar';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard requireAdmin>
      <div className="flex min-h-[calc(100vh-4rem)]">
        <AdminSidebar />
        <div className="flex-1 p-6 sm:p-8 bg-[#FAFAFA]">
          {children}
        </div>
      </div>
    </AuthGuard>
  );
}
