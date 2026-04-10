/**
 * @module ErrorPage
 * @description Global error boundary page shown when an unhandled error occurs.
 */
"use client";

import React from "react";
import Button from "@/components/ui/button";

/**
 * Renders an error message and a retry button.
 *
 * @param props.error - The caught Error object.
 * @param props.reset - Callback to reset the error boundary and retry.
 * @returns The error page element.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="text-5xl mb-4">⚠️</div>
      <h2 className="text-2xl font-bold text-gray-900">Something went wrong</h2>
      <p className="mt-2 text-gray-600 max-w-md">
        An unexpected error occurred. Please try again.
      </p>
      <Button className="mt-6" onClick={reset}>
        Try Again
      </Button>
    </div>
  );
}
