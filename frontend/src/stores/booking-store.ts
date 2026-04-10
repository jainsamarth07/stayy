/**
 * @module bookingStore
 * @description Zustand store managing booking list, selection, tab state, and loading.
 */
import { create } from "zustand";
import type { Booking } from "@/types";

/** State shape for the booking store. */
interface BookingState {
  bookings: Booking[];
  selectedBooking: Booking | null;
  activeTab: "upcoming" | "past" | "cancelled";
  loading: boolean;

  setBookings: (bookings: Booking[]) => void;
  setSelectedBooking: (booking: Booking | null) => void;
  setActiveTab: (tab: "upcoming" | "past" | "cancelled") => void;
  setLoading: (loading: boolean) => void;
  removeBooking: (id: string) => void;
}

/**
 * Global Zustand store for bookings.
 * Holds the booking list, active tab (upcoming/past/cancelled), and selection.
 */
export const useBookingStore = create<BookingState>((set) => ({
  bookings: [],
  selectedBooking: null,
  activeTab: "upcoming",
  loading: false,

  setBookings: (bookings) => set({ bookings }),
  setSelectedBooking: (selectedBooking) => set({ selectedBooking }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setLoading: (loading) => set({ loading }),
  removeBooking: (id) =>
    set((state) => ({
      bookings: state.bookings.filter((b) => b.id !== id),
    })),
}));
