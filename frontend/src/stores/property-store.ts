/**
 * @module propertyStore
 * @description Zustand store managing property listings, filters, and pagination state.
 */
import { create } from "zustand";
import type { Property } from "@/types";

/** Shape of the active property search filters. */
interface PropertyFilters {
  location: string;
  checkIn: string;
  checkOut: string;
  guests: number;
  minPrice: number;
  maxPrice: number;
  propertyType: string;
  amenities: string[];
  sortBy: string;
}

interface PropertyState {
  properties: Property[];
  selectedProperty: Property | null;
  filters: PropertyFilters;
  page: number;
  totalPages: number;
  loading: boolean;

  setProperties: (properties: Property[]) => void;
  setSelectedProperty: (property: Property | null) => void;
  setFilters: (filters: Partial<PropertyFilters>) => void;
  resetFilters: () => void;
  setPage: (page: number) => void;
  setTotalPages: (total: number) => void;
  setLoading: (loading: boolean) => void;
}

const defaultFilters: PropertyFilters = {
  location: "",
  checkIn: "",
  checkOut: "",
  guests: 1,
  minPrice: 0,
  maxPrice: 10000,
  propertyType: "",
  amenities: [],
  sortBy: "recommended",
};

/**
 * Global Zustand store for property listings.
 * Holds the current list, selected item, filter criteria, and pagination.
 */
export const usePropertyStore = create<PropertyState>((set) => ({
  properties: [],
  selectedProperty: null,
  filters: { ...defaultFilters },
  page: 1,
  totalPages: 1,
  loading: false,

  setProperties: (properties) => set({ properties }),
  setSelectedProperty: (selectedProperty) => set({ selectedProperty }),
  setFilters: (partial) =>
    set((state) => ({ filters: { ...state.filters, ...partial }, page: 1 })),
  resetFilters: () => set({ filters: { ...defaultFilters }, page: 1 }),
  setPage: (page) => set({ page }),
  setTotalPages: (totalPages) => set({ totalPages }),
  setLoading: (loading) => set({ loading }),
}));
