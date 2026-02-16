'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { onAuthStateChanged, type User } from 'firebase/auth';
import { auth } from '../firebase/config';
import { isAdmin } from '../firebase/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  isAdmin: false,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, isAdmin: isAdmin(user) }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
