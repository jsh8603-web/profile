'use client';

import Image from 'next/image';
import { User } from 'lucide-react';
import { useAuth } from '@/lib/context/AuthContext';

interface UserAvatarProps {
  size?: number;
  className?: string;
}

export default function UserAvatar({ size = 32, className = '' }: UserAvatarProps) {
  const { user } = useAuth();

  if (!user) return null;

  if (user.photoURL) {
    return (
      <Image
        src={user.photoURL}
        alt={user.displayName || 'User'}
        width={size}
        height={size}
        className={`rounded-full ${className}`}
      />
    );
  }

  return (
    <div
      className={`flex items-center justify-center rounded-full bg-[#0071E3] text-white ${className}`}
      style={{ width: size, height: size }}
    >
      {user.displayName ? (
        <span className="text-xs font-semibold">
          {user.displayName.charAt(0).toUpperCase()}
        </span>
      ) : (
        <User size={size * 0.5} />
      )}
    </div>
  );
}
