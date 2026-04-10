/** Unit tests for the {@link usePropertyStore} Zustand store. */
import { describe, it, expect, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { usePropertyStore } from "@/stores/property-store";

describe("usePropertyStore", () => {
  beforeEach(() => {
    const { resetFilters } = usePropertyStore.getState();
    act(() => {
      resetFilters();
      usePropertyStore.setState({ properties: [], loading: false });
    });
  });

  it("starts with default filters", () => {
    const { filters } = usePropertyStore.getState();
    expect(filters.location).toBe("");
    expect(filters.guests).toBe(1);
    expect(filters.sortBy).toBe("recommended");
  });

  it("setFilters merges partial filter updates", () => {
    act(() => {
      usePropertyStore.getState().setFilters({ location: "Miami", guests: 3 });
    });
    const { filters, page } = usePropertyStore.getState();
    expect(filters.location).toBe("Miami");
    expect(filters.guests).toBe(3);
    expect(filters.sortBy).toBe("recommended"); // unchanged
    expect(page).toBe(1); // reset to 1
  });

  it("resetFilters restores defaults", () => {
    act(() => {
      usePropertyStore.getState().setFilters({ location: "Paris", minPrice: 100 });
      usePropertyStore.getState().resetFilters();
    });
    const { filters } = usePropertyStore.getState();
    expect(filters.location).toBe("");
    expect(filters.minPrice).toBe(0);
  });

  it("setProperties updates the properties list", () => {
    act(() => {
      usePropertyStore.getState().setProperties([{ id: "1" } as any, { id: "2" } as any]);
    });
    expect(usePropertyStore.getState().properties).toHaveLength(2);
  });

  it("setLoading toggles loading state", () => {
    act(() => usePropertyStore.getState().setLoading(true));
    expect(usePropertyStore.getState().loading).toBe(true);

    act(() => usePropertyStore.getState().setLoading(false));
    expect(usePropertyStore.getState().loading).toBe(false);
  });
});
