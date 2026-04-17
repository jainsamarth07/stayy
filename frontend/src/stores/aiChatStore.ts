import { create } from "zustand";

interface AIChatState {
  isOpen: boolean;
  toggleChat: () => void;
  closeChat: () => void;
}

export const useAIChatStore = create<AIChatState>((set) => ({
  isOpen: false,
  toggleChat: () => set((s) => ({ isOpen: !s.isOpen })),
  closeChat: () => set({ isOpen: false }),
}));
