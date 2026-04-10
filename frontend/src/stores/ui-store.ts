/**
 * @module uiStore
 * @description Zustand store for global UI state such as sidebar and mobile menu toggles.
 */
import { create } from "zustand";

/** State shape for global UI toggles. */
interface UIState {
  sidebarOpen: boolean;
  mobileMenuOpen: boolean;

  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleMobileMenu: () => void;
  setMobileMenuOpen: (open: boolean) => void;
}

/**
 * Global Zustand store for UI toggles (sidebar, mobile menu).
 */
export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  mobileMenuOpen: false,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  toggleMobileMenu: () => set((s) => ({ mobileMenuOpen: !s.mobileMenuOpen })),
  setMobileMenuOpen: (mobileMenuOpen) => set({ mobileMenuOpen }),
}));
