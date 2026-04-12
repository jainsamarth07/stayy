"use client";

import React, { Suspense, useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import PropertyCard from "@/components/property/property-card";
import SearchBar, { SearchFilters } from "@/components/property/search-bar";
import { Pagination } from "@/components/ui/pagination";
import { Spinner } from "@/components/ui/index";
import EmptyState from "@/components/ui/empty-state";
import { propertyApi } from "@/lib/api";
import type { Property } from "@/types";
import { Search, Map, List } from "lucide-react";
import DynamicPropertyMap from "@/components/property/map/dynamic-map";

const defaultFilters: SearchFilters = {
  location: "",
  check_in: "",
  check_out: "",
  guests: 1,
  amenities: [],
};

export default function PropertiesPageWrapper() {
  return (
    <Suspense fallback={<div className="flex justify-center py-20"><Spinner size="lg" /></div>}>
      <PropertiesPage />
    </Suspense>
  );
}

function PropertiesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState("recommended");
  // Default to split — map on right, list on left
  const [viewMode, setViewMode] = useState<"list" | "split">("split");
  const [hoveredPropertyId, setHoveredPropertyId] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>(() => ({
    ...defaultFilters,
    location: searchParams.get("location") || "",
    check_in: searchParams.get("check_in") || "",
    check_out: searchParams.get("check_out") || "",
    guests: parseInt(searchParams.get("guests") || "1") || 1,
  }));

  // Map bounds — when set, only properties inside the viewport are shown in the list
  const [mapBounds, setMapBounds] = useState<{
    north: number; south: number; east: number; west: number;
  } | null>(null);

  // Properties filtered to the current map viewport
  const displayProperties = mapBounds
    ? properties.filter((p) => {
        if (p.latitude == null || p.longitude == null) return false;
        return (
          p.latitude <= mapBounds.north &&
          p.latitude >= mapBounds.south &&
          p.longitude <= mapBounds.east &&
          p.longitude >= mapBounds.west
        );
      })
    : properties;

  const fetchProperties = useCallback(async (currentPage: number) => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = {
        page: currentPage,
        page_size: 20,
      };
      if (filters.location) params.city = filters.location;
      if (filters.min_price) params.min_price = filters.min_price;
      if (filters.max_price) params.max_price = filters.max_price;
      if (filters.guests > 1) params.max_guests = filters.guests;

      const res = await propertyApi.search(params);
      const data = res.data;
      let items: Property[] = Array.isArray(data) ? data : data.items || [];

      if (sortBy === "price_low") {
        items = [...items].sort((a, b) => a.price_per_night - b.price_per_night);
      } else if (sortBy === "price_high") {
        items = [...items].sort((a, b) => b.price_per_night - a.price_per_night);
      } else if (sortBy === "newest") {
        items = [...items].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      }

      setProperties(items);
      setTotalPages(data.total_pages || Math.ceil((data.total || 20) / 20));
      // Clear stale bounds when new results load
      setMapBounds(null);
    } catch {
      setProperties([]);
    } finally {
      setLoading(false);
    }
  }, [filters, sortBy]);

  useEffect(() => {
    fetchProperties(page);
  }, [page, fetchProperties]);

  const handleSearch = () => {
    setPage(1);
    fetchProperties(1);
    const params = new URLSearchParams();
    if (filters.location) params.set("location", filters.location);
    if (filters.check_in) params.set("check_in", filters.check_in);
    if (filters.check_out) params.set("check_out", filters.check_out);
    if (filters.guests > 1) params.set("guests", String(filters.guests));
    router.push(`/properties?${params.toString()}`);
  };

  const handleBoundsChange = useCallback((bounds: {
    north: number; south: number; east: number; west: number;
  }) => {
    setMapBounds(bounds);
  }, []);

  const inMapArea = mapBounds !== null;

  return (
    <main className="min-h-screen bg-white flex flex-col">
      {/* Search section */}
      <div className="border-b py-4">
        <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20">
          <SearchBar
            filters={filters}
            onChange={setFilters}
            onSearch={handleSearch}
          />
        </div>
      </div>

      {/* Header */}
      <div className="border-b">
        <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">
                {filters.location ? `Stays in ${filters.location}` : "Explore all stays"}
              </h1>
              {!loading && (
                <p className="text-sm text-neutral-500 mt-1">
                  {inMapArea
                    ? `${displayProperties.length} of ${properties.length} properties in map area`
                    : `${properties.length} properties found`}
                </p>
              )}
            </div>

            <div className="flex items-center gap-3">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="text-sm border rounded-xl px-4 py-2.5 bg-white font-semibold focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-1"
              >
                <option value="recommended">Recommended</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
                <option value="rating">Top Rated</option>
                <option value="newest">Newest</option>
              </select>

              {/* List / Map+List toggle */}
              <div className="hidden md:flex items-center border rounded-xl overflow-hidden">
                <button
                  onClick={() => setViewMode("list")}
                  className={`flex items-center gap-1.5 px-3 py-2 text-sm font-semibold transition ${
                    viewMode === "list"
                      ? "bg-neutral-900 text-white"
                      : "bg-white text-neutral-600 hover:bg-neutral-50"
                  }`}
                >
                  <List className="h-4 w-4" />
                  <span>List</span>
                </button>
                <button
                  onClick={() => setViewMode("split")}
                  className={`flex items-center gap-1.5 px-3 py-2 text-sm font-semibold transition border-l ${
                    viewMode === "split"
                      ? "bg-neutral-900 text-white"
                      : "bg-white text-neutral-600 hover:bg-neutral-50"
                  }`}
                >
                  <Map className="h-4 w-4" />
                  <span>Map</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content — properties LEFT, map RIGHT */}
      <div className="flex-1 flex overflow-hidden">
        {/* Property list */}
        <div
          className={`overflow-y-auto py-8 ${
            viewMode === "split"
              ? "w-1/2 px-4 sm:px-6 border-r"
              : "w-full px-4 sm:px-8 md:px-10 xl:px-20 mx-auto max-w-container"
          }`}
        >
          {/* "Clear map filter" pill */}
          {inMapArea && (
            <div className="flex items-center gap-2 mb-5">
              <span className="text-xs text-neutral-500">Filtered by map area</span>
              <button
                onClick={() => setMapBounds(null)}
                className="text-xs font-semibold underline text-neutral-700 hover:text-neutral-900"
              >
                Clear
              </button>
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-20">
              <Spinner size="lg" />
            </div>
          ) : displayProperties.length === 0 ? (
            <EmptyState
              title={inMapArea ? "No properties in this area" : "No exact matches"}
              description={
                inMapArea
                  ? "Pan or zoom the map to explore more properties."
                  : "Try changing or removing some of your filters."
              }
              icon={<Search className="h-12 w-12 text-neutral-400" />}
            />
          ) : (
            <>
              <div
                className={`grid gap-x-5 gap-y-8 ${
                  viewMode === "split"
                    ? "grid-cols-1 lg:grid-cols-2"
                    : "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5"
                }`}
              >
                {displayProperties.map((property) => (
                  <div
                    key={property.id}
                    onMouseEnter={() => setHoveredPropertyId(property.id)}
                    onMouseLeave={() => setHoveredPropertyId(null)}
                  >
                    <PropertyCard property={property} />
                  </div>
                ))}
              </div>
              {!inMapArea && totalPages > 1 && (
                <Pagination
                  page={page}
                  totalPages={totalPages}
                  onPageChange={setPage}
                />
              )}
            </>
          )}
        </div>

        {/* Map — right side, sticky full-height, only in split mode */}
        {viewMode === "split" && (
          <div
            className="hidden md:block relative w-1/2"
            style={{ height: "calc(100vh - 178px)" }}
          >
            <div className="sticky top-0 h-full">
              <DynamicPropertyMap
                properties={properties}
                activePropertyId={hoveredPropertyId}
                onPropertyHover={setHoveredPropertyId}
                onBoundsChange={handleBoundsChange}
              />
            </div>
          </div>
        )}
      </div>

      {/* Mobile floating map toggle */}
      <div className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
        <button
          onClick={() => setViewMode((prev) => (prev === "list" ? "split" : "list"))}
          className="flex items-center gap-2 bg-neutral-900 text-white px-5 py-3 rounded-full shadow-xl text-sm font-semibold hover:bg-neutral-800 active:scale-95 transition"
        >
          {viewMode === "list" ? (
            <><Map className="h-4 w-4" /><span>Show map</span></>
          ) : (
            <><List className="h-4 w-4" /><span>Show list</span></>
          )}
        </button>
      </div>
    </main>
  );
}
