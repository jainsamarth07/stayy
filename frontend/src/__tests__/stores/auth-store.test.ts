/** Unit tests for the {@link useAuthStore} Zustand store. */
import { describe, it, expect, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { useAuthStore, type AuthUser } from "@/stores/auth-store";

const mockUser: AuthUser = {
  id: "1",
  email: "test@test.com",
  full_name: "Test User",
  name: "Test User",
  role: "user",
  backendId: null,
};

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.setState({ user: null, sessionToken: null, isAuthenticated: false, isLoading: true });
  });

  it("starts with null user and not authenticated", () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it("setSession with user sets authenticated", () => {
    act(() => {
      useAuthStore.getState().setSession(mockUser, "tok_123");
    });
    const state = useAuthStore.getState();
    expect(state.user).toBeTruthy();
    expect(state.sessionToken).toBe("tok_123");
    expect(state.isAuthenticated).toBe(true);
    expect(state.isLoading).toBe(false);
  });

  it("setSession with null clears authentication", () => {
    act(() => {
      useAuthStore.getState().setSession(mockUser, "tok_123");
    });
    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    act(() => {
      useAuthStore.getState().setSession(null, null);
    });
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().sessionToken).toBeNull();
  });

  it("logout clears all auth state", () => {
    act(() => {
      useAuthStore.getState().setSession(mockUser, "tok_123");
    });
    expect(useAuthStore.getState().isAuthenticated).toBe(true);

    act(() => {
      useAuthStore.getState().logout();
    });
    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().sessionToken).toBeNull();
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
  });

  it("setLoading toggles loading state", () => {
    act(() => {
      useAuthStore.getState().setLoading(false);
    });
    expect(useAuthStore.getState().isLoading).toBe(false);

    act(() => {
      useAuthStore.getState().setLoading(true);
    });
    expect(useAuthStore.getState().isLoading).toBe(true);
  });
});
