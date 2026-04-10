/**
 * Auth store — thin wrapper around BetterAuth session state.
 * Keeps the same public interface so existing components work unchanged.
 * The sessionToken is used by the API client as a Bearer token.
 */
import { create } from "zustand";

export interface AuthUser {
  id: string;
  /** UUID from the backend 'users' table — use for all API filters & comparisons */
  backendId: string | null;
  email: string;
  full_name: string;
  name: string;
  phone?: string | null;
  role: string;
  image?: string | null;
}

interface AuthState {
  user: AuthUser | null;
  sessionToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setSession: (user: AuthUser | null, token: string | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  sessionToken: null,
  isAuthenticated: false,
  isLoading: true,

  setSession: (user, token) =>
    set({
      user,
      sessionToken: token,
      isAuthenticated: !!user,
      isLoading: false,
    }),

  setLoading: (isLoading) => set({ isLoading }),

  logout: () =>
    set({ user: null, sessionToken: null, isAuthenticated: false, isLoading: false }),
}));
