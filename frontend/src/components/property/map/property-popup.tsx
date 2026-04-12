"use client";

/**
 * Map popup card — appears when a user clicks a price marker.
 * Displays property image, title, price, and a short description.
 * Clicking the card navigates to the property detail page.
 */

import React from "react";
import Link from "next/link";
import { X, Star } from "lucide-react";
import type { Property } from "@/types";

interface PropertyPopupProps {
  property: Property;
  onClose: () => void;
}

export default function PropertyPopup({ property, onClose }: PropertyPopupProps) {
  const mainImage =
    property.images?.[0]?.image_url || "/placeholder-property.svg";

  return (
    <div
      className="absolute bottom-6 left-4 z-[1000] w-72 animate-in slide-in-from-bottom-3 fade-in duration-200"
      data-testid="property-popup"
    >
      <div className="bg-white rounded-2xl shadow-2xl overflow-hidden border border-neutral-100">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-2.5 right-2.5 z-10 bg-white/90 backdrop-blur rounded-full p-1 hover:bg-white shadow-sm transition"
          aria-label="Close popup"
        >
          <X className="h-4 w-4 text-neutral-700" />
        </button>

        {/* Card — entire thing is a link */}
        <Link href={`/properties/${property.id}`} className="block">
          {/* Image */}
          <div className="relative aspect-[16/10] overflow-hidden">
            <img
              src={mainImage}
              alt={property.title}
              className="h-full w-full object-cover hover:scale-105 transition-transform duration-300"
            />
            {property.hourly_enabled && (
              <span className="absolute top-2 left-2 bg-white rounded-full px-2 py-0.5 text-[11px] font-bold shadow-sm">
                Hourly
              </span>
            )}
          </div>

          {/* Info */}
          <div className="p-3.5">
            {/* Title + rating */}
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-sm font-semibold text-neutral-900 line-clamp-1 leading-tight">
                {property.title}
              </h3>
              <div className="flex items-center gap-0.5 shrink-0">
                <Star className="h-3 w-3 fill-current text-neutral-900" />
                <span className="text-xs font-medium">New</span>
              </div>
            </div>

            {/* Location */}
            <p className="text-xs text-neutral-500 mt-0.5 line-clamp-1">
              {property.city}{property.address ? ` · ${property.address}` : ""}
            </p>

            {/* Description */}
            <p className="text-xs text-neutral-400 mt-1 line-clamp-2 leading-relaxed">
              {property.description}
            </p>

            {/* Price */}
            <div className="flex items-baseline gap-1 mt-2.5">
              <span className="text-sm font-bold text-neutral-900">
                ₹{property.price_per_night.toLocaleString()}
              </span>
              <span className="text-xs text-neutral-500">night</span>
              {property.hourly_config?.hourly_price && (
                <span className="text-xs text-neutral-400 ml-1">
                  · ₹{property.hourly_config.hourly_price}/hr
                </span>
              )}
            </div>

            {/* Guests */}
            <p className="text-[11px] text-neutral-400 mt-1">
              Up to {property.max_guests} guest{property.max_guests !== 1 ? "s" : ""}
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
}
