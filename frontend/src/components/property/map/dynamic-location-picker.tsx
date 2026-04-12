"use client";

/**
 * Dynamically-imported LocationPicker — avoids mapbox-gl SSR issues.
 * Usage:
 *   import DynamicLocationPicker from "@/components/property/map/dynamic-location-picker";
 */

import dynamic from "next/dynamic";
import { Spinner } from "@/components/ui/index";

const DynamicLocationPicker = dynamic(
  () => import("./location-picker"),
  {
    ssr: false,
    loading: () => (
      <div className="h-[400px] w-full flex items-center justify-center bg-neutral-50 rounded-xl border border-neutral-200">
        <Spinner size="lg" />
      </div>
    ),
  }
);

export default DynamicLocationPicker;
