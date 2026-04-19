"use client";

import React, { useState } from "react";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { Select } from "@/components/ui/index";
import { Search, SlidersHorizontal, X } from "lucide-react";

export interface SearchFilters {
  location: string;
  check_in: string;
  check_out: string;
  guests: number;
  min_price?: number;
  max_price?: number;
  property_type?: string;
  bedrooms?: number;
  amenities: string[];
}

interface SearchBarProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  onSearch: () => void;
  compact?: boolean;
}

const propertyTypes = [
  { value: "", label: "All types" },
  { value: "apartment", label: "Apartment" },
  { value: "house", label: "House" },
  { value: "villa", label: "Villa" },
  { value: "cabin", label: "Cabin" },
  { value: "studio", label: "Studio" },
  { value: "loft", label: "Loft" },
  { value: "cottage", label: "Cottage" },
];

const amenityOptions = [
  "WiFi", "Kitchen", "Parking", "Pool", "Hot Tub", "AC",
  "Washer", "Dryer", "Gym", "Pet Friendly", "Workspace",
  "TV", "Fireplace", "BBQ", "EV Charger",
];

export default function SearchBar({ filters, onChange, onSearch, compact }: SearchBarProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const update = (field: string, value: unknown) =>
    onChange({ ...filters, [field]: value });

  const toggleAmenity = (amenity: string) => {
    const current = filters.amenities;
    const next = current.includes(amenity)
      ? current.filter((a) => a !== amenity)
      : [...current, amenity];
    update("amenities", next);
  };

  if (compact) {
    return (
      <div className="flex items-center border rounded-full shadow-sm hover:shadow-md transition bg-white max-w-2xl mx-auto">
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-4 divide-x">
          <div className="px-6 py-3">
            <label className="block text-xs font-bold">Where</label>
            <input
              type="text"
              value={filters.location}
              onChange={(e) => update("location", e.target.value)}
              placeholder="Search destinations"
              className="w-full text-sm bg-transparent border-0 p-0 focus:outline-none focus:ring-0 placeholder:text-stone-400 text-stone-600"
            />
          </div>
          <div className="px-4 py-3 hidden sm:block">
            <label className="block text-xs font-bold">Check in</label>
            <input
              type="date"
              value={filters.check_in}
              onChange={(e) => update("check_in", e.target.value)}
              className="w-full text-sm bg-transparent border-0 p-0 focus:outline-none focus:ring-0 text-stone-600"
            />
          </div>
          <div className="px-4 py-3 hidden sm:block">
            <label className="block text-xs font-bold">Check out</label>
            <input
              type="date"
              value={filters.check_out}
              onChange={(e) => update("check_out", e.target.value)}
              className="w-full text-sm bg-transparent border-0 p-0 focus:outline-none focus:ring-0 text-stone-600"
            />
          </div>
          <div className="px-4 py-3 hidden sm:block">
            <label className="block text-xs font-bold">Guests</label>
            <input
              type="number"
              min={1}
              max={20}
              value={filters.guests}
              onChange={(e) => update("guests", parseInt(e.target.value) || 1)}
              className="w-full text-sm bg-transparent border-0 p-0 focus:outline-none focus:ring-0 text-stone-600"
            />
          </div>
        </div>
        <button
          onClick={onSearch}
          className="bg-primary-500 hover:bg-primary-600 text-white rounded-full p-3 m-2 transition-colors"
        >
          <Search className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border shadow-sm p-5 space-y-4">
      {/* Main search row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
        <Input
          label="Location"
          placeholder="City, state, or country"
          value={filters.location}
          onChange={(e) => update("location", e.target.value)}
          leftIcon={<Search className="h-4 w-4" />}
        />
        <Input
          label="Check in"
          type="date"
          value={filters.check_in}
          onChange={(e) => update("check_in", e.target.value)}
        />
        <Input
          label="Check out"
          type="date"
          value={filters.check_out}
          onChange={(e) => update("check_out", e.target.value)}
        />
        <Input
          label="Guests"
          type="number"
          min={1}
          max={20}
          value={filters.guests}
          onChange={(e) => update("guests", parseInt(e.target.value) || 1)}
        />
        <Button fullWidth onClick={onSearch}>
          <Search className="h-4 w-4 mr-2" />
          Search
        </Button>
      </div>

      {/* Filters toggle */}
      <button
        className="text-sm text-neutral-600 hover:text-neutral-900 font-semibold flex items-center gap-2 py-2 px-4 border rounded-xl hover:border-neutral-900 transition"
        onClick={() => setShowAdvanced(!showAdvanced)}
      >
        <SlidersHorizontal className="h-4 w-4" />
        Filters
        {showAdvanced && <X className="h-3 w-3 ml-1" />}
      </button>

      {/* Advanced filters */}
      {showAdvanced && (
        <div className="pt-4 border-t space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Select
              label="Property type"
              options={propertyTypes}
              value={filters.property_type || ""}
              onChange={(e) => update("property_type", e.target.value || undefined)}
            />
            <Input
              label="Min price / night"
              type="number"
              min={0}
              placeholder="₹0"
              value={filters.min_price ?? ""}
              onChange={(e) => update("min_price", parseInt(e.target.value) || undefined)}
            />
            <Input
              label="Max price / night"
              type="number"
              min={0}
              placeholder="No limit"
              value={filters.max_price ?? ""}
              onChange={(e) => update("max_price", parseInt(e.target.value) || undefined)}
            />
          </div>

          {/* Amenities */}
          <div>
            <label className="block text-sm font-semibold text-neutral-800 mb-2">
              Amenities
            </label>
            <div className="flex flex-wrap gap-2">
              {amenityOptions.map((amenity) => (
                <button
                  key={amenity}
                  type="button"
                  onClick={() => toggleAmenity(amenity)}
                  className={`px-4 py-2 rounded-full text-sm border transition-all ${
                    filters.amenities.includes(amenity)
                      ? "bg-neutral-900 border-neutral-900 text-white"
                      : "border-neutral-300 text-neutral-700 hover:border-neutral-900"
                  }`}
                >
                  {amenity}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
