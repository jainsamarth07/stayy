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
import { Search } from "lucide-react";

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
  const [filters, setFilters] = useState<SearchFilters>(() => ({
    ...defaultFilters,
    location: searchParams.get("location") || "",
    check_in: searchParams.get("check_in") || "",
    check_out: searchParams.get("check_out") || "",
    guests: parseInt(searchParams.get("guests") || "1") || 1,
  }));

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

  return (
    <main className="min-h-screen bg-white">
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

      {/* Results */}
      <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold">
              {filters.location
                ? `Stays in ${filters.location}`
                : "Explore all stays"}
            </h1>
            {!loading && (
              <p className="text-sm text-neutral-500 mt-1">
                {properties.length} properties found
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
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : properties.length === 0 ? (
          <EmptyState
            title="No exact matches"
            description="Try changing or removing some of your filters or adjusting your search area."
            icon={<Search className="h-12 w-12 text-neutral-400" />}
          />
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-x-6 gap-y-10">
              {properties.map((property) => (
                <PropertyCard key={property.id} property={property} />
              ))}
            </div>
            {totalPages > 1 && (
              <Pagination
                page={page}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            )}
          </>
        )}
      </div>
    </main>
  );
}
