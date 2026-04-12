"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Heart, ChevronLeft, ChevronRight, Star } from "lucide-react";
import { motion } from "framer-motion";
import type { Property } from "@/types";

interface PropertyCardProps {
  property: Property;
  showHost?: boolean;
}

export default function PropertyCard({ property, showHost = true }: PropertyCardProps) {
  const [imgIdx, setImgIdx] = useState(0);
  const [isFavorited, setIsFavorited] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const images = property.images?.length ? property.images : [];
  const mainImage = images[imgIdx]?.image_url || "/placeholder-property.svg";

  const prevImage = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setImgIdx((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  const nextImage = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setImgIdx((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Link
        href={`/properties/${property.id}`}
        className="group block"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Image */}
        <div className="relative aspect-square rounded-xl overflow-hidden bg-neutral-100">
          <img
            src={mainImage}
            alt={property.title}
            className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-500"
          />

          {/* Heart button - layered icons */}
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setIsFavorited(!isFavorited);
            }}
            className="absolute top-3 right-3 z-10 hover:scale-110 transition-transform"
            aria-label="Toggle favorite"
          >
            <Heart
              className="h-7 w-7 absolute top-0 left-0 text-white/70 drop-shadow-md"
              strokeWidth={2}
            />
            <Heart
              className={`h-7 w-7 relative transition-colors ${
                isFavorited ? "fill-rose-500 text-rose-500" : "fill-neutral-500/50 text-transparent"
              }`}
              strokeWidth={0}
            />
          </button>

          {/* Image nav arrows */}
          {images.length > 1 && isHovered && (
            <>
              <button
                onClick={prevImage}
                className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/90 rounded-full p-1 shadow-md hover:bg-white hover:scale-105 transition opacity-0 group-hover:opacity-100"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={nextImage}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/90 rounded-full p-1 shadow-md hover:bg-white hover:scale-105 transition opacity-0 group-hover:opacity-100"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </>
          )}

          {/* Dots */}
          {images.length > 1 && (
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
              {images.slice(0, 5).map((_, i) => (
                <span
                  key={i}
                  className={`h-1.5 w-1.5 rounded-full transition-all ${
                    i === imgIdx ? "bg-white scale-110" : "bg-white/60"
                  }`}
                />
              ))}
            </div>
          )}

          {/* Badge */}
          {property.hourly_enabled && (
            <span className="absolute top-3 left-3 bg-white rounded-full px-2.5 py-1 text-xs font-bold shadow-sm">
              Hourly
            </span>
          )}
        </div>

        {/* Details */}
        <div className="mt-3">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-[15px] font-semibold text-neutral-900 truncate">
              {property.city || property.title}
            </h3>
            <div className="flex items-center gap-1 shrink-0">
              <Star className="h-3.5 w-3.5 fill-current" />
              <span className="text-sm">New</span>
            </div>
          </div>
          <p className="text-sm text-neutral-500 truncate mt-0.5">
            {property.title}
          </p>
          <p className="text-sm text-neutral-500">
            Up to {property.max_guests} guests
          </p>
          <p className="mt-1.5">
            <span className="text-[15px] font-semibold">
              ₹{property.price_per_night}
            </span>
            <span className="text-[15px] text-neutral-500"> night</span>
            {property.hourly_config?.hourly_price && (
              <span className="text-sm text-neutral-400 ml-1.5">
                · ₹{property.hourly_config.hourly_price}/hr
              </span>
            )}
          </p>
        </div>
      </Link>
    </motion.div>
  );
}
