/**
 * @module StarRating
 * @description Star rating display and interactive rating input component.
 */
"use client";

import React from "react";

interface StarRatingProps {
  rating: number;
  maxStars?: number;
  size?: "sm" | "md" | "lg";
  interactive?: boolean;
  onRate?: (rating: number) => void;
}

const sizes = { sm: "h-4 w-4", md: "h-5 w-5", lg: "h-6 w-6" };

/**
 * Renders a row of star icons. Can be used as a read-only display or an interactive rating input.
 *
 * @param props.rating - Current rating value.
 * @param props.maxStars - Number of stars to render. Defaults to `5`.
 * @param props.size - Icon size preset. Defaults to `"md"`.
 * @param props.interactive - When `true`, stars become clickable.
 * @param props.onRate - Callback fired with the selected rating when `interactive` is enabled.
 * @returns The star rating element.
 */
export default function StarRating({
  rating,
  maxStars = 5,
  size = "md",
  interactive = false,
  onRate,
}: StarRatingProps) {
  const [hover, setHover] = React.useState(0);

  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: maxStars }, (_, i) => {
        const starValue = i + 1;
        const filled = interactive ? starValue <= (hover || rating) : starValue <= rating;
        const halfFilled = !interactive && !filled && starValue - 0.5 <= rating;

        return (
          <button
            key={i}
            type={interactive ? "button" : undefined}
            disabled={!interactive}
            onClick={() => onRate?.(starValue)}
            onMouseEnter={() => interactive && setHover(starValue)}
            onMouseLeave={() => interactive && setHover(0)}
            className={`${interactive ? "cursor-pointer" : "cursor-default"} focus:outline-none`}
          >
            <svg
              className={`${sizes[size]} ${
                filled
                  ? "text-yellow-400"
                  : halfFilled
                  ? "text-yellow-400"
                  : "text-gray-300"
              }`}
              fill={filled || halfFilled ? "currentColor" : "none"}
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={filled || halfFilled ? 0 : 1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
              />
            </svg>
          </button>
        );
      })}
    </div>
  );
}
