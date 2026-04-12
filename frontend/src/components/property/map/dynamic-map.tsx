"use client";

/**
 * Dynamically-imported PropertyMap component.
 * mapbox-gl accesses browser APIs at import time, so it must be loaded client-side only.
 * Import this file instead of directly importing PropertyMap.
 *
 * Usage:
 *   import DynamicPropertyMap from "@/components/property/map/dynamic-map";
 *   <DynamicPropertyMap properties={properties} />
 */

import dynamic from "next/dynamic";
import { Spinner } from "@/components/ui/index";

const DynamicPropertyMap = dynamic(
  () => import("./property-map"),
  {
    ssr: false,
    loading: () => (
      <div className="h-full w-full flex items-center justify-center bg-neutral-50 rounded-xl">
        <Spinner size="lg" />
      </div>
    ),
  }
);

export default DynamicPropertyMap;
