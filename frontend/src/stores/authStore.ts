// Zustand Store for Authentication (Demo Mode)
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  clearError: () => void;
}

// Demo user
const DEMO_USER: User = {
  id: 'demo-user-001',
  email: 'admin@doctor-doom.com',
  full_name: 'Demo Admin',
  role: 'admin',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Demo mode - accept any credentials
        const token = 'demo-token-' + Date.now();
        set({ 
          token, 
          isAuthenticated: true,
          user: DEMO_USER,
          isLoading: false 
        });
        
        console.log('✓ Demo login successful:', email);
      },

      register: async (email: string, password: string, fullName: string) => {
        set({ isLoading: true, error: null });
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Demo mode - auto login
        await get().login(email, password);
      },

      logout: async () => {
        console.log('✓ Demo logout');
        set({ user: null, token: null, isAuthenticated: false });
      },

      fetchUser: async () => {
        const token = get().token;
        if (!token) return;

        // Demo mode - use demo user
        set({ user: DEMO_USER, isAuthenticated: true });
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, isAuthenticated: state.isAuthenticated, user: state.user }),
    }
  )
);
