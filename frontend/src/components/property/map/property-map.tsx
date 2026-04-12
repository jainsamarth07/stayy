"use client";

/**
 * Interactive Mapbox property map — renders price markers on a react-map-gl Map.
 * Lazy-loaded via next/dynamic (see dynamic-map.tsx).
 *
 * Features:
 * - Price-tag markers on each property's lat/lng
 * - Click a marker → popup with image, title, price
 * - Auto-fits bounds to visible properties on load
 * - "Search this area" button after the user pans/zooms
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Map, { NavigationControl } from "react-map-gl";
import type { MapRef, ViewStateChangeEvent } from "react-map-gl";
import type { Property } from "@/types";
import PriceMarker from "./price-marker";
import PropertyPopup from "./property-popup";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
const MAP_STYLE = "mapbox://styles/mapbox/streets-v12";
const DEFAULT_LAT = 20.5937;  // India — roughly central
const DEFAULT_LNG = 78.9629;
const DEFAULT_ZOOM = 4;

interface PropertyMapProps {
  properties: Property[];
  onBoundsChange?: (bounds: {
    north: number;
    south: number;
    east: number;
    west: number;
  }) => void;
  activePropertyId?: string | null;
  onPropertyHover?: (propertyId: string | null) => void;
}

function filterGeoProperties(properties: Property[]): Property[] {
  return properties.filter(
    (p) =>
      p.latitude != null &&
      p.longitude != null &&
      !isNaN(p.latitude) &&
      !isNaN(p.longitude)
  );
}

export default function PropertyMap({
  properties,
  onBoundsChange,
  activePropertyId = null,
  onPropertyHover,
}: PropertyMapProps) {
  const mapRef = useRef<MapRef>(null);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [showSearchArea, setShowSearchArea] = useState(false);
  const [mapLoaded, setMapLoaded] = useState(false);

  const geoProperties = useMemo(() => filterGeoProperties(properties), [properties]);

  const initialViewState = useMemo(() => {
    if (geoProperties.length === 0) {
      return { longitude: DEFAULT_LNG, latitude: DEFAULT_LAT, zoom: DEFAULT_ZOOM };
    }
    const avgLat =
      geoProperties.reduce((s, p) => s + p.latitude!, 0) / geoProperties.length;
    const avgLng =
      geoProperties.reduce((s, p) => s + p.longitude!, 0) / geoProperties.length;
    return { longitude: avgLng, latitude: avgLat, zoom: DEFAULT_ZOOM };
  }, [geoProperties]);

  // Fit bounds once the map is loaded and we have geo-tagged properties
  useEffect(() => {
    if (!mapLoaded || geoProperties.length === 0) return;
    const lngs = geoProperties.map((p) => p.longitude!);
    const lats = geoProperties.map((p) => p.latitude!);
    mapRef.current?.fitBounds(
      [
        [Math.min(...lngs), Math.min(...lats)],
        [Math.max(...lngs), Math.max(...lats)],
      ],
      { padding: 60, maxZoom: 14, duration: 1000 }
    );
  }, [mapLoaded, geoProperties]);

  const handleMoveEnd = useCallback((_e: ViewStateChangeEvent) => {
    setShowSearchArea(true);
  }, []);

  const handleSearchThisArea = useCallback(() => {
    const bounds = mapRef.current?.getBounds();
    if (!bounds || !onBoundsChange) return;
    onBoundsChange({
      north: bounds.getNorth(),
      south: bounds.getSouth(),
      east: bounds.getEast(),
      west: bounds.getWest(),
    });
    setShowSearchArea(false);
  }, [onBoundsChange]);

  return (
    <div className="relative h-full w-full" data-testid="property-map">
      <Map
        ref={mapRef}
        initialViewState={initialViewState}
        style={{ width: "100%", height: "100%" }}
        mapStyle={MAP_STYLE}
        mapboxAccessToken={MAPBOX_TOKEN}
        onMoveEnd={handleMoveEnd}
        onLoad={() => setMapLoaded(true)}
        onClick={() => setSelectedProperty(null)}
        reuseMaps
      >
        <NavigationControl position="top-right" showCompass={false} />

        {geoProperties.map((property) => (
          <PriceMarker
            key={property.id}
            property={property}
            isActive={activePropertyId === property.id}
            isSelected={selectedProperty?.id === property.id}
            onClick={(p) =>
              setSelectedProperty((prev) =>
                prev?.id === p.id ? null : p
              )
            }
            onHover={onPropertyHover}
          />
        ))}
      </Map>

      {/* "Search this area" floating button */}
      {showSearchArea && onBoundsChange && (
        <button
          onClick={handleSearchThisArea}
          className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-white text-neutral-900 text-sm font-semibold px-5 py-2.5 rounded-full shadow-lg border border-neutral-200 hover:bg-neutral-50 hover:shadow-xl transition-all active:scale-95"
        >
          Search this area
        </button>
      )}

      {/* Property popup card */}
      {selectedProperty && (
        <PropertyPopup
          property={selectedProperty}
          onClose={() => setSelectedProperty(null)}
        />
      )}

      {/* Empty-state overlay when no properties have coordinates */}
      {geoProperties.length === 0 && properties.length > 0 && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/60 backdrop-blur-sm pointer-events-none">
          <div className="bg-white rounded-2xl shadow-lg px-8 py-6 text-center max-w-xs">
            <p className="text-neutral-900 font-semibold">No map data available</p>
            <p className="text-neutral-500 text-sm mt-1">
              These properties don&apos;t have location coordinates yet.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
