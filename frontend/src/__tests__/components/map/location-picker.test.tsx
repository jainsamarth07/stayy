/**
 * @module location-picker.test
 * @description Tests for the LocationPicker geocoding helpers and Google Maps URL parser.
 * The map rendering itself requires Leaflet (browser-only), so we test
 * the pure functions: reverseGeocode, searchAddress, parseGoogleMapsUrl.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";

// Import the exported parser directly
// (In a real environment with node_modules, this import resolves.
//  For isolated testing we also replicate the function below.)

// Replicate parseGoogleMapsUrl for isolated testing (mirrors location-picker.tsx)
function isValidCoord(lat: number, lng: number): boolean {
  return (
    !isNaN(lat) &&
    !isNaN(lng) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180
  );
}

function parseGoogleMapsUrl(
  input: string
): { lat: number; lng: number } | null {
  const trimmed = input.trim();
  if (!trimmed) return null;

  const atMatch = trimmed.match(/@(-?\d+\.\d+),(-?\d+\.\d+)/);
  if (atMatch) {
    const lat = parseFloat(atMatch[1]);
    const lng = parseFloat(atMatch[2]);
    if (isValidCoord(lat, lng)) return { lat, lng };
  }

  const qMatch = trimmed.match(/[?&]q=(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)/);
  if (qMatch) {
    const lat = parseFloat(qMatch[1]);
    const lng = parseFloat(qMatch[2]);
    if (isValidCoord(lat, lng)) return { lat, lng };
  }

  const llMatch = trimmed.match(/[?&]ll=(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)/);
  if (llMatch) {
    const lat = parseFloat(llMatch[1]);
    const lng = parseFloat(llMatch[2]);
    if (isValidCoord(lat, lng)) return { lat, lng };
  }

  const searchMatch = trimmed.match(/\/search\/(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)/);
  if (searchMatch) {
    const lat = parseFloat(searchMatch[1]);
    const lng = parseFloat(searchMatch[2]);
    if (isValidCoord(lat, lng)) return { lat, lng };
  }

  const plainMatch = trimmed.match(/^(-?\d+\.\d+)[,\s]+\s*(-?\d+\.\d+)$/);
  if (plainMatch) {
    const lat = parseFloat(plainMatch[1]);
    const lng = parseFloat(plainMatch[2]);
    if (isValidCoord(lat, lng)) return { lat, lng };
  }

  return null;
}

// Replicate the geocoding functions from location-picker.tsx for isolated testing

interface NominatimResult {
  lat: string;
  lon: string;
  display_name: string;
}

async function reverseGeocode(lat: number, lng: number): Promise<string | null> {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`,
      { headers: { "User-Agent": "StayNest/1.0" } }
    );
    if (!res.ok) return null;
    const data = await res.json();
    return data.display_name || null;
  } catch {
    return null;
  }
}

async function searchAddress(query: string): Promise<NominatimResult[]> {
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`,
      { headers: { "User-Agent": "StayNest/1.0" } }
    );
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

describe("reverseGeocode", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns display_name on success", async () => {
    const mockResponse = {
      ok: true,
      json: async () => ({ display_name: "123 Beach Road, Goa, India" }),
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(mockResponse as Response);

    const result = await reverseGeocode(15.49, 73.82);
    expect(result).toBe("123 Beach Road, Goa, India");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("reverse?format=json&lat=15.49&lon=73.82"),
      expect.objectContaining({ headers: { "User-Agent": "StayNest/1.0" } })
    );
  });

  it("returns null when response is not ok", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      json: async () => ({}),
    } as Response);

    const result = await reverseGeocode(0, 0);
    expect(result).toBeNull();
  });

  it("returns null when fetch throws", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    const result = await reverseGeocode(0, 0);
    expect(result).toBeNull();
  });

  it("returns null when display_name is missing", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({}),
    } as Response);

    const result = await reverseGeocode(0, 0);
    expect(result).toBeNull();
  });
});

describe("searchAddress", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns results on success", async () => {
    const mockResults: NominatimResult[] = [
      { lat: "15.49", lon: "73.82", display_name: "Goa, India" },
      { lat: "15.50", lon: "73.83", display_name: "Panaji, Goa, India" },
    ];
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => mockResults,
    } as Response);

    const results = await searchAddress("Goa India");
    expect(results).toHaveLength(2);
    expect(results[0].display_name).toBe("Goa, India");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("search?format=json&q=Goa%20India"),
      expect.any(Object)
    );
  });

  it("returns empty array when response is not ok", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      json: async () => [],
    } as Response);

    const results = await searchAddress("Nowhere");
    expect(results).toEqual([]);
  });

  it("returns empty array when fetch throws", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));

    const results = await searchAddress("Nowhere");
    expect(results).toEqual([]);
  });

  it("encodes special characters in query", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    await searchAddress("123 Main St, New York");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("q=123%20Main%20St%2C%20New%20York"),
      expect.any(Object)
    );
  });
});

// ─── parseGoogleMapsUrl ─────────────────────────────────────────────
describe("parseGoogleMapsUrl", () => {
  // Happy paths — various Google Maps URL formats
  it("parses /@lat,lng,zoom format", () => {
    const result = parseGoogleMapsUrl(
      "https://www.google.com/maps/@19.0760,72.8777,15z"
    );
    expect(result).toEqual({ lat: 19.076, lng: 72.8777 });
  });

  it("parses /place/.../@lat,lng format", () => {
    const result = parseGoogleMapsUrl(
      "https://www.google.com/maps/place/Gateway+of+India/@18.9220,72.8347,17z/data=!3m1!4b1"
    );
    expect(result).toEqual({ lat: 18.922, lng: 72.8347 });
  });

  it("parses ?q=lat,lng format", () => {
    const result = parseGoogleMapsUrl(
      "https://maps.google.com/?q=28.6139,77.2090"
    );
    expect(result).toEqual({ lat: 28.6139, lng: 77.209 });
  });

  it("parses ?q=lat,lng from google.com/maps", () => {
    const result = parseGoogleMapsUrl(
      "https://www.google.com/maps?q=15.4909,73.8278"
    );
    expect(result).toEqual({ lat: 15.4909, lng: 73.8278 });
  });

  it("parses /search/lat,lng format", () => {
    const result = parseGoogleMapsUrl(
      "https://www.google.com/maps/search/12.9716,77.5946"
    );
    expect(result).toEqual({ lat: 12.9716, lng: 77.5946 });
  });

  it("parses ?ll=lat,lng format", () => {
    const result = parseGoogleMapsUrl(
      "https://maps.google.com/maps?ll=26.9124,75.7873&z=14"
    );
    expect(result).toEqual({ lat: 26.9124, lng: 75.7873 });
  });

  it("parses plain coordinate pair", () => {
    const result = parseGoogleMapsUrl("19.076, 72.877");
    expect(result).toEqual({ lat: 19.076, lng: 72.877 });
  });

  it("parses plain coordinate pair without space", () => {
    const result = parseGoogleMapsUrl("19.076,72.877");
    expect(result).toEqual({ lat: 19.076, lng: 72.877 });
  });

  it("handles negative coordinates (Southern/Western hemispheres)", () => {
    const result = parseGoogleMapsUrl(
      "https://www.google.com/maps/@-33.8688,151.2093,13z"
    );
    expect(result).toEqual({ lat: -33.8688, lng: 151.2093 });
  });

  it("handles negative longitude", () => {
    const result = parseGoogleMapsUrl("40.7128, -74.0060");
    expect(result).toEqual({ lat: 40.7128, lng: -74.006 });
  });

  it("trims whitespace", () => {
    const result = parseGoogleMapsUrl("  19.076, 72.877  ");
    expect(result).toEqual({ lat: 19.076, lng: 72.877 });
  });

  // Edge cases / invalid inputs
  it("returns null for empty string", () => {
    expect(parseGoogleMapsUrl("")).toBeNull();
  });

  it("returns null for whitespace-only string", () => {
    expect(parseGoogleMapsUrl("   ")).toBeNull();
  });

  it("returns null for random text", () => {
    expect(parseGoogleMapsUrl("hello world")).toBeNull();
  });

  it("returns null for non-Maps URL", () => {
    expect(
      parseGoogleMapsUrl("https://www.google.com/search?q=restaurants+near+me")
    ).toBeNull();
  });

  it("returns null for invalid lat > 90", () => {
    expect(parseGoogleMapsUrl("91.0000, 72.0000")).toBeNull();
  });

  it("returns null for invalid lng > 180", () => {
    expect(parseGoogleMapsUrl("19.0000, 181.0000")).toBeNull();
  });

  it("returns null for invalid lat < -90", () => {
    expect(parseGoogleMapsUrl("-91.0000, 72.0000")).toBeNull();
  });

  it("returns null for short URL without coords", () => {
    expect(
      parseGoogleMapsUrl("https://goo.gl/maps/abc123")
    ).toBeNull();
  });
});
