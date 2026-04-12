"use client";

import React from "react";
import { X, Grid3x3 } from "lucide-react";

interface ImageGalleryProps {
  images: { url: string; caption?: string }[];
  title: string;
}

export default function ImageGallery({ images, title }: ImageGalleryProps) {
  const [showAll, setShowAll] = React.useState(false);
  const displayImages = images.length > 0 ? images : [{ url: "/placeholder-property.svg" }];

  if (showAll) {
    return (
      <div className="fixed inset-0 z-50 bg-white overflow-y-auto">
        <div className="sticky top-0 bg-white border-b z-10 px-6 py-4 flex items-center">
          <button
            onClick={() => setShowAll(false)}
            className="flex items-center gap-2 text-sm font-semibold hover:bg-neutral-100 rounded-full p-2 transition"
          >
            <X className="h-5 w-5" />
          </button>
          <span className="ml-4 text-sm font-semibold">
            {displayImages.length} photos
          </span>
        </div>
        <div className="max-w-3xl mx-auto px-4 py-8 space-y-3">
          {displayImages.map((img, i) => (
            <div key={i}>
              <img
                src={img.url}
                alt={img.caption || `${title} - Photo ${i + 1}`}
                className="w-full rounded-lg object-cover"
              />
              {img.caption && (
                <p className="text-sm text-neutral-500 mt-2 px-1">{img.caption}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      {displayImages.length === 1 ? (
        <div className="aspect-[16/9] rounded-xl overflow-hidden bg-neutral-100 cursor-pointer" onClick={() => setShowAll(true)}>
          <img
            src={displayImages[0].url}
            alt={title}
            className="h-full w-full object-cover hover:opacity-90 transition"
          />
        </div>
      ) : (
        <div className="grid grid-cols-4 grid-rows-2 gap-2 rounded-xl overflow-hidden h-[60vh] max-h-[500px]">
          {/* Main image */}
          <div className="col-span-2 row-span-2 bg-neutral-100 cursor-pointer" onClick={() => setShowAll(true)}>
            <img
              src={displayImages[0].url}
              alt={title}
              className="h-full w-full object-cover hover:brightness-90 transition"
            />
          </div>
          {/* Side images */}
          {displayImages.slice(1, 5).map((img, i) => (
            <div key={i} className="bg-neutral-100 cursor-pointer" onClick={() => setShowAll(true)}>
              <img
                src={img.url}
                alt={`${title} - ${i + 2}`}
                className="h-full w-full object-cover hover:brightness-90 transition"
              />
            </div>
          ))}
        </div>
      )}

      {/* Show all button */}
      {displayImages.length > 1 && (
        <button
          onClick={() => setShowAll(true)}
          className="absolute bottom-4 right-4 bg-white border border-neutral-900 rounded-lg px-4 py-1.5 text-sm font-semibold flex items-center gap-2 hover:bg-neutral-50 transition"
        >
          <Grid3x3 className="h-4 w-4" />
          Show all photos
        </button>
      )}
    </div>
  );
}
