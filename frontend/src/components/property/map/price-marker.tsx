"use client";

/**
 * Floating price-tag marker for the Mapbox property map.
 * Uses react-map-gl Marker with a plain React element — no DivIcon hacks.
 */

import React from "react";
import { Marker } from "react-map-gl";
import type { Property } from "@/types";

interface PriceMarkerProps {
  property: Property;
  isActive?: boolean;
  isSelected?: boolean;
  onClick: (property: Property) => void;
  onHover?: (propertyId: string | null) => void;
}

function formatPrice(price: number): string {
  if (price >= 100000) return `₹${(price / 100000).toFixed(1)}L`;
  if (price >= 1000) return `₹${(price / 1000).toFixed(price >= 10000 ? 0 : 1)}K`;
  return `₹${price}`;
}

export default function PriceMarker({
  property,
  isActive = false,
  isSelected = false,
  onClick,
  onHover,
}: PriceMarkerProps) {
  const label = formatPrice(property.price_per_night);
  const highlighted = isSelected || isActive;

  return (
    <Marker
      longitude={property.longitude!}
      latitude={property.latitude!}
      anchor="bottom"
    >
      <div
        onClick={(e) => {
          e.stopPropagation();
          onClick(property);
        }}
        onMouseEnter={() => onHover?.(property.id)}
        onMouseLeave={() => onHover?.(null)}
        className={[
          "relative cursor-pointer select-none",
          "px-2.5 py-1.5 rounded-xl text-xs font-bold",
          "transition-all duration-150",
          highlighted
            ? "bg-neutral-900 text-white shadow-xl scale-110"
            : "bg-white text-neutral-900 shadow-md border border-neutral-200 hover:scale-105 hover:shadow-lg",
        ].join(" ")}
        style={{ zIndex: highlighted ? 10 : 1 }}
      >
        {label}
        {/* Downward arrow */}
        <div
          className={[
            "absolute left-1/2 -translate-x-1/2 -bottom-[5px]",
            "w-2.5 h-2.5 rotate-45",
            highlighted
              ? "bg-neutral-900"
              : "bg-white border-b border-r border-neutral-200",
          ].join(" ")}
        />
      </div>
    </Marker>
  );
}
