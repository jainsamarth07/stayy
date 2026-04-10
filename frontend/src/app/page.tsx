"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import SearchBar, { type SearchFilters } from "@/components/property/search-bar";
import PropertyCard from "@/components/property/property-card";
import Button from "@/components/ui/button";
import { propertyApi } from "@/lib/api";
import type { Property } from "@/types";
import {
  Palmtree, Building2, TreePine, Waves, Mountain, Tent, Castle,
  Snowflake, Gem, Warehouse, Sun, Sailboat, Flame, Home, Fish,
} from "lucide-react";

const CATEGORIES = [
  { icon: Palmtree, label: "Beach" },
  { icon: Building2, label: "Modern" },
  { icon: TreePine, label: "Countryside" },
  { icon: Waves, label: "Pools" },
  { icon: Sailboat, label: "Islands" },
  { icon: Fish, label: "Lake" },
  { icon: Snowflake, label: "Skiing" },
  { icon: Castle, label: "Castles" },
  { icon: Mountain, label: "Caves" },
  { icon: Tent, label: "Camping" },
  { icon: Sun, label: "Desert" },
  { icon: Warehouse, label: "Barns" },
  { icon: Gem, label: "Lux" },
  { icon: Home, label: "Cabins" },
  { icon: Flame, label: "Trending" },
];

export default function HomePage() {
  const [featured, setFeatured] = useState<Property[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({
    location: "",
    check_in: "",
    check_out: "",
    guests: 1,
    amenities: [],
  });

  useEffect(() => {
    const loadFeatured = async () => {
      try {
        const res = await propertyApi.search({ page_size: 12 });
        const data = res.data;
        setFeatured(Array.isArray(data) ? data : data.items || []);
      } catch {
        setFeatured([]);
      } finally {
        setIsLoading(false);
      }
    };
    loadFeatured();
  }, []);

  return (
    <>
      {/* Search hero */}
      <section className="border-b bg-white pt-4 pb-2">
        <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20">
          <div className="md:hidden mb-4">
            <SearchBar
              compact
              filters={searchFilters}
              onChange={setSearchFilters}
              onSearch={() => {
                const params = new URLSearchParams();
                if (searchFilters.location) params.set("location", searchFilters.location);
                if (searchFilters.check_in) params.set("check_in", searchFilters.check_in);
                if (searchFilters.check_out) params.set("check_out", searchFilters.check_out);
                if (searchFilters.guests > 1) params.set("guests", String(searchFilters.guests));
                window.location.href = `/properties${params.toString() ? `?${params}` : ""}`;
              }}
            />
          </div>

          {/* Category bar */}
          <div className="flex items-center gap-8 overflow-x-auto scrollbar-hide py-3">
            {CATEGORIES.map((c) => {
              const Icon = c.icon;
              const isActive = activeCategory === c.label;
              return (
                <button
                  key={c.label}
                  onClick={() => setActiveCategory(isActive ? null : c.label)}
                  className={`flex flex-col items-center gap-2 min-w-fit pb-3 border-b-2 transition-all cursor-pointer ${
                    isActive
                      ? "border-neutral-800 text-neutral-800"
                      : "border-transparent text-neutral-500 hover:text-neutral-800 hover:border-neutral-300"
                  }`}
                >
                  <Icon className="h-6 w-6" strokeWidth={1.5} />
                  <span className="text-xs font-semibold whitespace-nowrap">{c.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      {/* Properties grid */}
      <section className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 pt-8 pb-12">
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-6">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="aspect-square rounded-xl bg-neutral-200" />
                <div className="mt-3 space-y-2">
                  <div className="h-4 w-3/4 rounded bg-neutral-200" />
                  <div className="h-3 w-1/2 rounded bg-neutral-200" />
                  <div className="h-3 w-1/3 rounded bg-neutral-200" />
                </div>
              </div>
            ))}
          </div>
        ) : featured.length === 0 ? (
          <div className="text-center py-16">
            <h2 className="text-xl font-semibold text-neutral-700">No stays found</h2>
            <p className="mt-2 text-neutral-500">Check back soon — new properties are added regularly.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-x-6 gap-y-10">
            {featured.map((p) => (
              <PropertyCard key={p.id} property={p} />
            ))}
          </div>
        )}
      </section>

      {/* How It Works */}
      <section className="bg-neutral-50 py-20 border-t">
        <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20">
          <h2 className="text-2xl font-bold text-center mb-12">How StayNest Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 max-w-4xl mx-auto">
            {[
              { step: "1", title: "Search & Discover", desc: "Browse thousands of unique homes and filter by location, dates, or amenities." },
              { step: "2", title: "Book Instantly", desc: "Reserve your stay with secure payments — or message the host directly." },
              { step: "3", title: "Enjoy Your Stay", desc: "Check in, relax, and leave a review to help the community." },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-rose-50 text-rose-500 font-bold text-lg mb-4">
                  {item.step}
                </div>
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm text-neutral-500 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Host CTA */}
      <section className="bg-neutral-900 py-16">
        <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 text-center text-white">
          <h2 className="text-3xl font-bold">Try Hosting</h2>
          <p className="mt-3 text-lg opacity-80 max-w-xl mx-auto">
            Keep 100% of your rental revenue with our membership-based model. Plans start at just ₹2,499/month.
          </p>
          <Link href="/auth/register?role=host">
            <Button variant="secondary" size="lg" className="mt-8 bg-white text-neutral-900 hover:bg-neutral-100">
              Learn more
            </Button>
          </Link>
        </div>
      </section>
    </>
  );
}
