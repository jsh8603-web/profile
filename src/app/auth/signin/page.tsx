'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Mail, Lock, Chrome, AlertCircle } from 'lucide-react';
import { signInWithGoogle, signInWithEmail, signUpWithEmail } from '@/lib/firebase/auth';
import { useAuth } from '@/lib/context/AuthContext';
import { Button } from '@/components/ui';

export default function SignInPage() {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { user } = useAuth();

  if (user) {
    router.push('/');
    return null;
  }

  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (mode === 'signup') {
        await signUpWithEmail(email, password);
      } else {
        await signInWithEmail(email, password);
      }
      router.push('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError('');
    setLoading(true);
    try {
      await signInWithGoogle();
      router.push('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-5">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[#1D1D1F]">
            {mode === 'signin' ? 'Welcome Back' : 'Create Account'}
          </h1>
          <p className="mt-2 text-sm text-[#86868B]">
            {mode === 'signin'
              ? 'Sign in to leave comments and interact'
              : 'Create an account to get started'}
          </p>
        </div>

        <div className="card-flat p-8">
          {/* Google Sign In */}
          <button
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl border border-[#D2D2D7] bg-white text-sm font-medium text-[#1D1D1F] hover:bg-[#F5F5F7] transition-colors disabled:opacity-50"
          >
            <Chrome size={18} />
            Continue with Google
          </button>

          {/* Divider */}
          <div className="flex items-center gap-4 my-6">
            <div className="flex-1 h-px bg-[#E8E8ED]" />
            <span className="text-xs text-[#86868B]">or</span>
            <div className="flex-1 h-px bg-[#E8E8ED]" />
          </div>

          {/* Email/Password Form */}
          <form onSubmit={handleEmailAuth} className="space-y-4">
            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#86868B]" />
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#D2D2D7] bg-white text-sm text-[#1D1D1F] placeholder:text-[#86868B] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all"
              />
            </div>

            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#86868B]" />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#D2D2D7] bg-white text-sm text-[#1D1D1F] placeholder:text-[#86868B] focus:outline-none focus:ring-2 focus:ring-[#0071E3]/30 focus:border-[#0071E3] transition-all"
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-red-50 text-red-600 text-sm">
                <AlertCircle size={16} />
                {error}
              </div>
            )}

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Loading...' : mode === 'signin' ? 'Sign In' : 'Create Account'}
            </Button>
          </form>

          {/* Toggle mode */}
          <p className="mt-6 text-center text-sm text-[#86868B]">
            {mode === 'signin' ? "Don't have an account?" : 'Already have an account?'}{' '}
            <button
              onClick={() => { setMode(mode === 'signin' ? 'signup' : 'signin'); setError(''); }}
              className="text-[#0071E3] font-medium hover:underline"
            >
              {mode === 'signin' ? 'Sign Up' : 'Sign In'}
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
