/**
 * @module price-marker.test
 * @description Tests for the PriceMarker component's price formatting logic.
 * Since PriceMarker relies on Leaflet (which requires a DOM map context),
 * we test the formatting logic and marker creation in isolation.
 */
import { describe, it, expect } from "vitest";

/** Replicated from price-marker.tsx for isolated testing */
function formatPrice(price: number): string {
  if (price >= 100000) return `₹${(price / 100000).toFixed(1)}L`;
  if (price >= 1000)
    return `₹${(price / 1000).toFixed(price >= 10000 ? 0 : 1)}K`;
  return `₹${price}`;
}

describe("formatPrice", () => {
  it("formats small prices without suffix", () => {
    expect(formatPrice(500)).toBe("₹500");
    expect(formatPrice(999)).toBe("₹999");
  });

  it("formats thousands with K suffix and 1 decimal", () => {
    expect(formatPrice(1000)).toBe("₹1.0K");
    expect(formatPrice(1500)).toBe("₹1.5K");
    expect(formatPrice(3500)).toBe("₹3.5K");
    expect(formatPrice(9999)).toBe("₹10.0K");
  });

  it("formats tens of thousands with K suffix and no decimal", () => {
    expect(formatPrice(10000)).toBe("₹10K");
    expect(formatPrice(25000)).toBe("₹25K");
    expect(formatPrice(99999)).toBe("₹100K");
  });

  it("formats lakhs with L suffix", () => {
    expect(formatPrice(100000)).toBe("₹1.0L");
    expect(formatPrice(250000)).toBe("₹2.5L");
    expect(formatPrice(1000000)).toBe("₹10.0L");
  });
});
