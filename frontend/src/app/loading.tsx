/**
 * @module Loading
 * @description Global loading fallback shown during route transitions.
 */
import React from "react";
import { Spinner } from "@/components/ui/index";

/**
 * Renders a centred spinner for full-page loading states.
 * @returns Loading spinner element.
 */
export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Spinner size="lg" />
    </div>
  );
}
