/**
 * @module EditPropertyPage
 * @description Edit form for an existing property listing, pre-populated with current data.
 */
"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { Spinner, Select, Textarea } from "@/components/ui/index";
import { toast } from "@/components/ui/toast";
import { propertyApi } from "@/lib/api";
import DynamicLocationPicker from "@/components/property/map/dynamic-location-picker";

const AMENITIES_LIST = [
  "WiFi", "Kitchen", "Free Parking", "Pool", "Hot Tub", "Air Conditioning",
  "Heating", "Washer", "Dryer", "TV", "Gym", "Elevator", "Pet Friendly",
];

export default function EditPropertyPage() {
  const params = useParams();
  const router = useRouter();
  const propertyId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [form, setForm] = useState({
    title: "",
    description: "",
    address: "",
    city: "",
    latitude: "",
    longitude: "",
    price_per_night: "",
    max_guests: "1",
    amenities: [] as string[],
  });

  useEffect(() => {
    const load = async () => {
      try {
        const res = await propertyApi.getById(propertyId);
        const data = res.data;
        setForm({
          title: data.title || "",
          description: data.description || "",
          address: data.address || "",
          city: data.city || "",
          latitude: data.latitude?.toString() || "",
          longitude: data.longitude?.toString() || "",
          price_per_night: data.price_per_night?.toString() || "",
          max_guests: data.max_guests?.toString() || "1",
          amenities: data.amenities || [],
        });
      } catch {
        toast.error("Property not found");
        router.push("/dashboard/properties");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [propertyId, router]);

  const update = (field: string, value: string | string[]) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const toggleAmenity = (a: string) =>
    update(
      "amenities",
      form.amenities.includes(a)
        ? form.amenities.filter((x) => x !== a)
        : [...form.amenities, a]
    );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        title: form.title,
        description: form.description,
        address: form.address,
        city: form.city,
        latitude: form.latitude ? parseFloat(form.latitude) : undefined,
        longitude: form.longitude ? parseFloat(form.longitude) : undefined,
        price_per_night: parseFloat(form.price_per_night),
        max_guests: parseInt(form.max_guests),
        amenities: form.amenities,
      };
      await propertyApi.update(propertyId, payload);
      toast.success("Property updated successfully");
      router.push("/dashboard/properties");
    } catch {
      toast.error("Failed to update property");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Edit Property</h2>
        <Button variant="outline" size="sm" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Details */}
        <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h3 className="font-semibold text-gray-900">Basic Details</h3>
          <Input
            label="Title"
            value={form.title}
            onChange={(e) => update("title", e.target.value)}
            required
          />
          <Textarea
            label="Description"
            value={form.description}
            onChange={(e) => update("description", e.target.value)}
            rows={4}
          />
        </section>

        {/* Location */}
        <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h3 className="font-semibold text-gray-900">Location</h3>
          <Input label="Address" value={form.address} onChange={(e) => update("address", e.target.value)} />
          <Input label="City" value={form.city} onChange={(e) => update("city", e.target.value)} required />

          {/* Interactive map picker */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pin your property on the map
            </label>
            <DynamicLocationPicker
              latitude={form.latitude ? parseFloat(form.latitude) : null}
              longitude={form.longitude ? parseFloat(form.longitude) : null}
              initialCity={form.city || undefined}
              onLocationChange={(lat, lng) => {
                update("latitude", lat.toString());
                update("longitude", lng.toString());
              }}
              onAddressSuggestion={(address) => {
                if (!form.address.trim()) {
                  update("address", address);
                }
              }}
            />
          </div>
        </section>

        {/* Pricing & Capacity */}
        <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h3 className="font-semibold text-gray-900">Pricing & Capacity</h3>
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Price per Night ($)"
              type="number"
              value={form.price_per_night}
              onChange={(e) => update("price_per_night", e.target.value)}
              required
            />
            <Input
              label="Max Guests"
              type="number"
              value={form.max_guests}
              onChange={(e) => update("max_guests", e.target.value)}
            />
          </div>
        </section>

        {/* Amenities */}
        <section className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Amenities</h3>
          <div className="flex flex-wrap gap-2">
            {AMENITIES_LIST.map((a) => (
              <button
                key={a}
                type="button"
                onClick={() => toggleAmenity(a)}
                className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                  form.amenities.includes(a)
                    ? "bg-primary-50 border-primary-300 text-primary-700"
                    : "bg-white border-gray-300 text-gray-600 hover:border-gray-400"
                }`}
              >
                {a}
              </button>
            ))}
          </div>
        </section>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Button variant="outline" type="button" onClick={() => router.back()}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            Save Changes
          </Button>
        </div>
      </form>
    </div>
  );
}
