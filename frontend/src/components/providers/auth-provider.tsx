"use client";

import React, { useEffect, createContext, useContext } from "react";
import { useSession } from "@/lib/auth-client";
import { useAuthStore, type AuthUser } from "@/stores/auth-store";
import { profileApi } from "@/lib/api";
import { useRouter, usePathname } from "next/navigation";
import { Spinner } from "@/components/ui/index";

interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextValue>({
  isAuthenticated: false,
  isLoading: true,
});

export function useAuth() {
  return useContext(AuthContext);
}

/**
 * Hydrates the Zustand auth store from BetterAuth's useSession hook.
 * This bridges BetterAuth sessions with all existing components that
 * depend on useAuthStore.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { data: session, isPending } = useSession();
  const { setSession, setLoading } = useAuthStore();

  useEffect(() => {
    if (isPending) {
      setLoading(true);
      return;
    }

    if (session?.user) {
      // BetterAuth's user type doesn't include custom fields at compile time;
      // cast through unknown to access the additionalFields we configured.
      const u = session.user as unknown as {
        id: string;
        email: string;
        name: string;
        image?: string | null;
        role?: string;
        phone?: string | null;
      };
      setSession(
        {
          id: u.id,
          backendId: null,
          email: u.email,
          full_name: u.name || u.email,
          name: u.name || u.email,
          role: u.role ?? "user",
          phone: u.phone ?? null,
          image: u.image ?? null,
        },
        session.session.token
      );

      // Fetch the backend UUID (from the 'users' table) so all
      // comparisons / filters against backend data work correctly.
      profileApi.get().then((res) => {
        const me = res.data;
        if (me?.id) {
          useAuthStore.getState().setSession(
            {
              id: u.id,
              backendId: me.id,
              email: u.email,
              full_name: me.full_name || u.name || u.email,
              name: u.name || u.email,
              role: me.role || u.role || "user",
              phone: me.phone ?? u.phone ?? null,
              image: u.image ?? null,
            },
            session.session.token
          );
        }
      }).catch(() => { /* backend unreachable — backendId stays null */ });
    } else {
      setSession(null, null);
    }
  }, [session, isPending, setSession, setLoading]);

  if (isPending) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{ isAuthenticated: !!session?.user, isLoading: isPending }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Protects a route — redirects to login if unauthenticated.
 */
export function ProtectedRoute({
  children,
  requiredRole,
}: {
  children: React.ReactNode;
  requiredRole?: "user" | "host" | "admin";
}) {
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace(`/auth/login?redirect=${encodeURIComponent(pathname)}`);
      return;
    }
    if (requiredRole && user?.role !== requiredRole && user?.role !== "admin") {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, user, requiredRole, router, pathname]);

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  return <>{children}</>;
}
