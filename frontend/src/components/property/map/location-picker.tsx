"use client";

/**
 * Interactive Mapbox location picker for property creation/edit.
 * Uses OpenStreetMap Nominatim for free geocoding (no API key needed).
 *
 * Features:
 * - Click-to-place pin on the map
 * - Draggable marker for fine-tuning
 * - Address search bar (geocoding via Nominatim)
 * - Reverse-geocodes pin position back to an address suggestion
 * - Paste Google Maps / short URL → auto-extract coordinates
 * - Auto-centers on the host's city if provided
 */

import React, { useCallback, useEffect, useRef, useState } from "react";
import Map, { Marker, NavigationControl } from "react-map-gl";
import type { MapRef, MapMouseEvent, MarkerDragEvent } from "react-map-gl";
import { MapPin, Search, X, Crosshair, Link2, Navigation } from "lucide-react";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
const MAP_STYLE = "mapbox://styles/mapbox/streets-v12";
const DEFAULT_LAT = 20.5937;
const DEFAULT_LNG = 78.9629;
const DEFAULT_ZOOM = 4;
const PLACED_ZOOM = 15;

interface LocationPickerProps {
  latitude: number | null;
  longitude: number | null;
  onLocationChange: (lat: number, lng: number) => void;
  onAddressSuggestion?: (address: string) => void;
  initialCity?: string;
  height?: string;
}

/** Nominatim search result shape */
interface NominatimResult {
  lat: string;
  lon: string;
  display_name: string;
}

/**
 * Parse a Google Maps URL and extract latitude/longitude.
 * Supports full Google Maps URLs and plain coordinate pairs.
 * Short URLs (maps.app.goo.gl) are resolved server-side before calling this.
 */
export function parseGoogleMapsUrl(
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

function isValidCoord(lat: number, lng: number): boolean {
  return (
    !isNaN(lat) && !isNaN(lng) &&
    lat >= -90 && lat <= 90 &&
    lng >= -180 && lng <= 180
  );
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

export default function LocationPicker({
  latitude,
  longitude,
  onLocationChange,
  onAddressSuggestion,
  initialCity,
  height = "400px",
}: LocationPickerProps) {
  const mapRef = useRef<MapRef>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<NominatimResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [gmapsUrl, setGmapsUrl] = useState("");
  const [gmapsError, setGmapsError] = useState("");
  const [mapLoaded, setMapLoaded] = useState(false);
  const cityInitialized = useRef(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const hasPosition = latitude !== null && longitude !== null;

  // Center on city once when map first loads (if no pin yet)
  useEffect(() => {
    if (!mapLoaded || cityInitialized.current || hasPosition || !initialCity) return;
    cityInitialized.current = true;
    searchAddress(initialCity).then((results) => {
      if (results.length > 0) {
        mapRef.current?.flyTo({
          center: [parseFloat(results[0].lon), parseFloat(results[0].lat)],
          zoom: 12,
          duration: 1000,
        });
      }
    });
  }, [mapLoaded, hasPosition, initialCity]);

  // Fly to position when it changes externally (e.g. Google Maps paste)
  const prevPosition = useRef<{ lat: number | null; lng: number | null }>({ lat: latitude, lng: longitude });
  useEffect(() => {
    if (!mapLoaded || !hasPosition) return;
    const prev = prevPosition.current;
    if (prev.lat === latitude && prev.lng === longitude) return;
    prevPosition.current = { lat: latitude, lng: longitude };
    mapRef.current?.flyTo({
      center: [longitude!, latitude!],
      zoom: PLACED_ZOOM,
      duration: 1200,
    });
  }, [mapLoaded, latitude, longitude, hasPosition]);

  // Map click → place pin
  const handleMapClick = useCallback(
    async (e: MapMouseEvent) => {
      const { lng, lat } = e.lngLat;
      onLocationChange(lat, lng);
      if (onAddressSuggestion) {
        const address = await reverseGeocode(lat, lng);
        if (address) onAddressSuggestion(address);
      }
    },
    [onLocationChange, onAddressSuggestion]
  );

  // Marker drag end → update pin
  const handleMarkerDrag = useCallback(
    async (e: MarkerDragEvent) => {
      const { lng, lat } = e.lngLat;
      onLocationChange(lat, lng);
      if (onAddressSuggestion) {
        const address = await reverseGeocode(lat, lng);
        if (address) onAddressSuggestion(address);
      }
    },
    [onLocationChange, onAddressSuggestion]
  );

  // Debounced address search
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    if (value.trim().length < 3) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }
    searchTimeoutRef.current = setTimeout(async () => {
      setIsSearching(true);
      const results = await searchAddress(value);
      setSearchResults(results);
      setShowResults(results.length > 0);
      setIsSearching(false);
    }, 400);
  }, []);

  const handleSelectResult = useCallback(
    (result: NominatimResult) => {
      const lat = parseFloat(result.lat);
      const lng = parseFloat(result.lon);
      onLocationChange(lat, lng);
      onAddressSuggestion?.(result.display_name);
      setSearchQuery(result.display_name);
      setShowResults(false);
    },
    [onLocationChange, onAddressSuggestion]
  );

  const clearSearch = () => {
    setSearchQuery("");
    setSearchResults([]);
    setShowResults(false);
  };

  // Handle Google Maps URL paste (including short goo.gl links)
  const handleGmapsUrl = useCallback(
    async (value: string) => {
      setGmapsUrl(value);
      setGmapsError("");
      if (!value.trim()) return;

      const isShortUrl = /^https?:\/\/(maps\.app\.goo\.gl|goo\.gl\/maps)\//i.test(value.trim());
      if (isShortUrl || /^https?:\/\/goo\.gl\//i.test(value.trim())) {
        try {
          const res = await fetch(`/api/resolve-maps?url=${encodeURIComponent(value.trim())}`);
          const data = await res.json();
          if (data.resolvedUrl) {
            const coords = parseGoogleMapsUrl(data.resolvedUrl);
            if (coords) {
              onLocationChange(coords.lat, coords.lng);
              if (onAddressSuggestion) {
                const address = await reverseGeocode(coords.lat, coords.lng);
                if (address) onAddressSuggestion(address);
              }
              return;
            }
          }
        } catch { /* fall through */ }
        setGmapsError("Could not resolve short URL. Try sharing the full link from Google Maps.");
        return;
      }

      const parsed = parseGoogleMapsUrl(value);
      if (parsed) {
        onLocationChange(parsed.lat, parsed.lng);
        if (onAddressSuggestion) {
          const address = await reverseGeocode(parsed.lat, parsed.lng);
          if (address) onAddressSuggestion(address);
        }
      } else if (value.trim().length > 5) {
        setGmapsError("Could not extract coordinates. Paste a Google Maps link or plain coordinates like 19.076, 72.877");
      }
    },
    [onLocationChange, onAddressSuggestion]
  );

  return (
    <div className="space-y-3" data-testid="location-picker">
      {/* Google Maps URL paste */}
      <div>
        <div className="relative">
          <Link2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <input
            type="text"
            value={gmapsUrl}
            onChange={(e) => handleGmapsUrl(e.target.value)}
            onPaste={(e) => {
              const pasted = e.clipboardData.getData("text");
              if (pasted) {
                e.preventDefault();
                setGmapsUrl(pasted);
                handleGmapsUrl(pasted);
              }
            }}
            placeholder="Paste Google Maps link or coordinates (e.g. 19.076, 72.877)"
            className="w-full pl-10 pr-10 py-2.5 text-sm border border-neutral-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-1 bg-white"
          />
          {gmapsUrl && (
            <button
              onClick={() => { setGmapsUrl(""); setGmapsError(""); }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        {gmapsError && <p className="text-xs text-red-500 mt-1">{gmapsError}</p>}
      </div>

      {/* Divider */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px bg-neutral-200" />
        <span className="text-xs text-neutral-400 font-medium">or search by address</span>
        <div className="flex-1 h-px bg-neutral-200" />
      </div>

      {/* Address search */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            onFocus={() => searchResults.length > 0 && setShowResults(true)}
            placeholder="Search for an address or place..."
            className="w-full pl-10 pr-10 py-2.5 text-sm border border-neutral-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-1 bg-white"
          />
          {searchQuery && (
            <button
              onClick={clearSearch}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {showResults && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-neutral-200 rounded-xl shadow-lg max-h-60 overflow-y-auto">
            {searchResults.map((result, i) => (
              <button
                key={`${result.lat}-${result.lon}-${i}`}
                onClick={() => handleSelectResult(result)}
                className="w-full text-left px-4 py-2.5 text-sm hover:bg-neutral-50 transition flex items-start gap-2 border-b border-neutral-50 last:border-0"
              >
                <MapPin className="h-4 w-4 text-neutral-400 mt-0.5 shrink-0" />
                <span className="line-clamp-2 text-neutral-700">{result.display_name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <p className="text-xs text-neutral-500 flex items-center gap-1">
        <Crosshair className="h-3 w-3" />
        Paste a Google Maps link, search an address, or click the map to drop a pin.
      </p>

      {/* Map */}
      <div
        className="rounded-xl overflow-hidden border border-neutral-200"
        style={{ height }}
      >
        <Map
          ref={mapRef}
          initialViewState={{
            longitude: hasPosition ? longitude! : DEFAULT_LNG,
            latitude: hasPosition ? latitude! : DEFAULT_LAT,
            zoom: hasPosition ? PLACED_ZOOM : DEFAULT_ZOOM,
          }}
          style={{ width: "100%", height: "100%" }}
          mapStyle={MAP_STYLE}
          mapboxAccessToken={MAPBOX_TOKEN}
          onClick={handleMapClick}
          onLoad={() => setMapLoaded(true)}
          cursor={hasPosition ? "default" : "crosshair"}
        >
          <NavigationControl position="top-right" showCompass={false} />

          {hasPosition && (
            <Marker
              longitude={longitude!}
              latitude={latitude!}
              anchor="bottom"
              draggable
              onDragEnd={handleMarkerDrag}
            >
              <div className="flex flex-col items-center">
                <Navigation
                  className="h-8 w-8 text-rose-600 drop-shadow-lg"
                  fill="currentColor"
                  strokeWidth={1}
                />
              </div>
            </Marker>
          )}
        </Map>
      </div>

      {/* Coordinate readout */}
      {hasPosition && (
        <div className="flex items-center gap-4 text-xs text-neutral-500 bg-neutral-50 rounded-lg px-3 py-2">
          <span><strong>Lat:</strong> {latitude!.toFixed(6)}</span>
          <span><strong>Lng:</strong> {longitude!.toFixed(6)}</span>
          <span className="text-green-600 font-medium flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            Location set
          </span>
        </div>
      )}

      {isSearching && <p className="text-xs text-neutral-400">Searching...</p>}
    </div>
  );
}
