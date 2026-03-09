import { create } from 'zustand';
import type { AuthUser } from '@/types/index';

interface AuthState {
  user: AuthUser | null;
  authenticated: boolean;
  loading: boolean;
  setUser: (user: AuthUser | null) => void;
  setAuthenticated: (authenticated: boolean) => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  authenticated: false,
  loading: true,
  setUser: (user) => set({ user }),
  setAuthenticated: (authenticated) => set({ authenticated }),
  setLoading: (loading) => set({ loading }),
}));
