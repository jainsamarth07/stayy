"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import SearchBar, { type SearchFilters } from "@/components/property/search-bar";
import PropertyCard from "@/components/property/property-card";
import Button from "@/components/ui/button";
import { propertyApi } from "@/lib/api";
import type { Property } from "@/types";
import { MapPin } from "lucide-react";

const DESTINATIONS = [
  { name: "Goa", image: "/placeholder-property.svg" },
  { name: "Manali", image: "/placeholder-property.svg" },
  { name: "Jaipur", image: "/placeholder-property.svg" },
  { name: "Pondicherry", image: "/placeholder-property.svg" },
  { name: "Ooty", image: "/placeholder-property.svg" },
  { name: "Shimla", image: "/placeholder-property.svg" },
];

export default function HomePage() {
  const [featured, setFeatured] = useState<Property[]>([]);
  const [isLoading, setIsLoading] = useState(true);
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
      <section className="bg-gradient-to-b from-primary-50/60 to-[#FFFAF5] pt-12 pb-10">
        <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20">
          <div className="max-w-2xl mx-auto text-center mb-8">
            <h1 className="text-3xl sm:text-4xl font-bold text-stone-900 tracking-tight">
              Find your perfect stay
            </h1>
            <p className="mt-3 text-stone-500 text-lg">
              Unique homes, zero commissions — explore stays curated just for you.
            </p>
          </div>
          <div className="max-w-3xl mx-auto">
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
        </div>
      </section>

      {/* Destination cards */}
      <section className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 py-10">
        <h2 className="text-xl font-bold text-stone-900 mb-6">Popular destinations</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
          {DESTINATIONS.map((d) => (
            <Link
              key={d.name}
              href={`/properties?location=${encodeURIComponent(d.name)}`}
              className="group relative aspect-[4/3] rounded-2xl overflow-hidden bg-stone-100"
            >
              <img src={d.image} alt={d.name} className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300" />
              <div className="absolute inset-0 bg-gradient-to-t from-stone-900/60 to-transparent" />
              <div className="absolute bottom-3 left-3 flex items-center gap-1.5 text-white">
                <MapPin className="h-4 w-4" />
                <span className="text-sm font-semibold">{d.name}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Properties grid */}
      <section className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 pt-2 pb-12">
        <h2 className="text-xl font-bold text-stone-900 mb-6">Featured stays</h2>
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="aspect-[4/3] rounded-2xl bg-stone-200" />
                <div className="mt-3 space-y-2">
                  <div className="h-4 w-3/4 rounded bg-stone-200" />
                  <div className="h-3 w-1/2 rounded bg-stone-200" />
                  <div className="h-3 w-1/3 rounded bg-stone-200" />
                </div>
              </div>
            ))}
          </div>
        ) : featured.length === 0 ? (
          <div className="text-center py-16">
            <h2 className="text-xl font-semibold text-stone-700">No stays found</h2>
            <p className="mt-2 text-stone-500">Check back soon — new properties are added regularly.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-10">
            {featured.map((p) => (
              <PropertyCard key={p.id} property={p} />
            ))}
          </div>
        )}
      </section>

      {/* How It Works */}
      <section className="bg-stone-50 py-20 border-t border-stone-200">
        <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20">
          <h2 className="text-2xl font-bold text-center mb-12">How StayNest Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 max-w-4xl mx-auto">
            {[
              { step: "1", title: "Search & Discover", desc: "Browse thousands of unique homes and filter by location, dates, or amenities." },
              { step: "2", title: "Book Instantly", desc: "Reserve your stay with secure payments — or message the host directly." },
              { step: "3", title: "Enjoy Your Stay", desc: "Check in, relax, and leave a review to help the community." },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary-50 text-primary-500 font-bold text-lg mb-4">
                  {item.step}
                </div>
                <h3 className="text-lg font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm text-stone-500 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Host CTA */}
      <section className="bg-stone-900 py-16">
        <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 text-center text-white">
          <h2 className="text-3xl font-bold">Start Hosting</h2>
          <p className="mt-3 text-lg opacity-80 max-w-xl mx-auto">
            Keep 100% of your rental revenue with our membership-based model. Plans start at just ₹2,499/month.
          </p>
          <Link href="/auth/register?role=host">
            <Button variant="secondary" size="lg" className="mt-8 bg-white text-stone-900 hover:bg-stone-100">
              Learn more
            </Button>
          </Link>
        </div>
      </section>
    </>
  );
}
