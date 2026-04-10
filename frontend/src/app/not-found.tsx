/**
 * @module NotFound
 * @description Custom 404 page displayed when a route does not exist.
 */
"use client";

import React from "react";
import Link from "next/link";
import Button from "@/components/ui/button";

/**
 * Renders a 404 "Page Not Found" message with a link back to the home page.
 * @returns The 404 page element.
 */
export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <h1 className="text-7xl font-bold text-gray-200">404</h1>
      <h2 className="mt-4 text-2xl font-bold text-gray-900">Page Not Found</h2>
      <p className="mt-2 text-gray-600 max-w-md">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <Link href="/" className="mt-6">
        <Button>Back to Home</Button>
      </Link>
    </div>
  );
}
