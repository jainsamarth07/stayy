/**
 * @module NewPropertyPage
 * @description Multi-step form for hosts to create a new property listing.
 */
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { Select, Textarea } from "@/components/ui/index";
import { toast } from "@/components/ui/toast";
import { propertyApi } from "@/lib/api";

const propertyTypes = [
  { value: "apartment", label: "Apartment" },
  { value: "house", label: "House" },
  { value: "villa", label: "Villa" },
  { value: "cabin", label: "Cabin" },
  { value: "studio", label: "Studio" },
  { value: "loft", label: "Loft" },
  { value: "cottage", label: "Cottage" },
  { value: "condo", label: "Condo" },
];

const amenityOptions = [
  "WiFi", "Kitchen", "Free Parking", "Pool", "Hot Tub", "Air Conditioning",
  "Washer", "Dryer", "Gym", "Pet Friendly", "Dedicated Workspace",
  "TV", "Fireplace", "BBQ Grill", "EV Charger", "Elevator",
  "Doorman", "Security Camera", "Smoke Alarm", "First Aid Kit",
];

export default function NewPropertyPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    title: "",
    description: "",
    property_type: "apartment",
    address: "",
    city: "",
    state: "",
    country: "",
    zip_code: "",
    latitude: "",
    longitude: "",
    nightly_price: "",
    bedrooms: "1",
    bathrooms: "1",
    max_guests: "2",
    amenities: [] as string[],
    house_rules: "",
    // Hourly config
    enable_hourly: false,
    hourly_rate: "",
    min_hours: "2",
    max_hours: "12",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [images, setImages] = useState<{ file: File; preview: string; isPrimary: boolean }[]>([]);

  const update = (field: string, value: unknown) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const toggleAmenity = (amenity: string) => {
    const next = form.amenities.includes(amenity)
      ? form.amenities.filter((a) => a !== amenity)
      : [...form.amenities, amenity];
    update("amenities", next);
  };

  const addImages = (files: FileList | null) => {
    if (!files) return;
    const newImages = Array.from(files)
      .filter((f) => f.type.startsWith("image/"))
      .map((file) => ({
        file,
        preview: URL.createObjectURL(file),
        isPrimary: false,
      }));
    setImages((prev) => {
      const combined = [...prev, ...newImages];
      // Auto-set first image as primary if none selected
      if (combined.length > 0 && !combined.some((img) => img.isPrimary)) {
        combined[0].isPrimary = true;
      }
      return combined;
    });
  };

  const removeImage = (index: number) => {
    setImages((prev) => {
      const next = prev.filter((_, i) => i !== index);
      // Revoke object URL to free memory
      URL.revokeObjectURL(prev[index].preview);
      // If removed image was primary, assign to first remaining
      if (prev[index].isPrimary && next.length > 0) {
        next[0].isPrimary = true;
      }
      return next;
    });
  };

  const setPrimaryImage = (index: number) => {
    setImages((prev) =>
      prev.map((img, i) => ({ ...img, isPrimary: i === index }))
    );
  };

  const validateStep = (s: number): boolean => {
    const errs: Record<string, string> = {};
    if (s === 1) {
      if (!form.title.trim()) errs.title = "Title is required";
      else if (form.title.trim().length < 3) errs.title = "Title must be at least 3 characters";
      if (!form.description.trim()) errs.description = "Description is required";
      else if (form.description.trim().length < 10) errs.description = "Description must be at least 10 characters";
      if (parseInt(form.max_guests) > 50) errs.max_guests = "Maximum 50 guests allowed";
    }
    if (s === 2) {
      if (!form.address.trim()) errs.address = "Address is required";
      else if (form.address.trim().length < 5) errs.address = "Address must be at least 5 characters";
      if (!form.city.trim()) errs.city = "City is required";
    }
    if (s === 3) {
      if (!form.nightly_price || parseFloat(form.nightly_price) <= 0)
        errs.nightly_price = "Valid price required";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateStep(3)) return;
    setLoading(true);
    try {
      const payload = {
        title: form.title,
        description: form.description,
        address: form.address,
        city: form.city,
        latitude: form.latitude ? parseFloat(form.latitude) : undefined,
        longitude: form.longitude ? parseFloat(form.longitude) : undefined,
        price_per_night: parseFloat(form.nightly_price),
        max_guests: parseInt(form.max_guests),
        amenities: form.amenities,
      };
      const created = await propertyApi.create(payload);
      const propertyId = created.data.id;

      // Upload images
      if (images.length > 0) {
        for (const img of images) {
          try {
            await propertyApi.uploadImage(propertyId, img.file, img.isPrimary);
          } catch {
            toast.error(`Failed to upload ${img.file.name}`);
          }
        }
      }

      // Configure hourly booking via separate endpoint if enabled
      if (form.enable_hourly && form.hourly_rate) {
        await propertyApi.configureHourly(propertyId, {
          hourly_price: parseFloat(form.hourly_rate),
          min_hours: parseInt(form.min_hours),
          max_hours: parseInt(form.max_hours),
        });
      }

      toast.success("Listing created!");
      router.push(`/properties/${propertyId}`);
    } catch (err: unknown) {
      // Extract message from Axios error or generic Error
      const axiosErr = err as { response?: { status?: number; data?: { detail?: string } } };
      const status = axiosErr?.response?.status;
      const detail = axiosErr?.response?.data?.detail;

      if (status === 402 || detail?.toLowerCase().includes("membership")) {
        toast.error("An active membership is required to create listings. Please subscribe to a plan first.");
      } else {
        toast.error(detail || (err instanceof Error ? err.message : "Failed to create listing"));
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-2">Create New Listing</h2>
      <p className="text-sm text-gray-500 mb-6">
        Fill in the details to list your property on StayNest.
      </p>

      {/* Progress */}
      <div className="flex items-center gap-2 mb-8">
        {["Details", "Location", "Pricing & Rules", "Photos"].map((label, i) => (
          <React.Fragment key={label}>
            <div className="flex items-center gap-2">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step > i + 1
                    ? "bg-green-100 text-green-700"
                    : step === i + 1
                    ? "bg-rose-600 text-white"
                    : "bg-gray-100 text-gray-400"
                }`}
              >
                {step > i + 1 ? "✓" : i + 1}
              </div>
              <span
                className={`text-sm font-medium hidden sm:block ${
                  step === i + 1 ? "text-gray-900" : "text-gray-400"
                }`}
              >
                {label}
              </span>
            </div>
            {i < 3 && <div className="flex-1 h-px bg-gray-200" />}
          </React.Fragment>
        ))}
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-6">
        {/* Step 1: Details */}
        {step === 1 && (
          <div className="space-y-4">
            <Input
              label="Property title"
              placeholder="e.g., Sunny Downtown Loft with City Views"
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              error={errors.title}
            />
            <Textarea
              label="Description"
              placeholder="Describe your property — what makes it unique?"
              rows={5}
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              error={errors.description}
            />
            <Select
              label="Property type"
              options={propertyTypes}
              value={form.property_type}
              onChange={(e) => update("property_type", e.target.value)}
            />
            <div className="grid grid-cols-3 gap-3">
              <Input
                label="Bedrooms"
                type="number"
                min={0}
                value={form.bedrooms}
                onChange={(e) => update("bedrooms", e.target.value)}
              />
              <Input
                label="Bathrooms"
                type="number"
                min={1}
                value={form.bathrooms}
                onChange={(e) => update("bathrooms", e.target.value)}
              />
              <Input
                label="Max guests"
                type="number"
                min={1}
                max={50}
                value={form.max_guests}
                onChange={(e) => update("max_guests", e.target.value)}
                error={errors.max_guests}
              />
            </div>

            {/* Amenities */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Amenities
              </label>
              <div className="flex flex-wrap gap-2">
                {amenityOptions.map((amenity) => (
                  <button
                    key={amenity}
                    type="button"
                    onClick={() => toggleAmenity(amenity)}
                    className={`px-3 py-1.5 rounded-full text-sm border transition ${
                      form.amenities.includes(amenity)
                        ? "bg-rose-50 border-rose-300 text-rose-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300"
                    }`}
                  >
                    {amenity}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Location */}
        {step === 2 && (
          <div className="space-y-4">
            <Input
              label="Street address"
              placeholder="123 Main Street"
              value={form.address}
              onChange={(e) => update("address", e.target.value)}
              error={errors.address}
            />
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="City"
                value={form.city}
                onChange={(e) => update("city", e.target.value)}
                error={errors.city}
              />
              <Input
                label="State / Province"
                value={form.state}
                onChange={(e) => update("state", e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Country"
                value={form.country}
                onChange={(e) => update("country", e.target.value)}
                error={errors.country}
              />
              <Input
                label="Zip code"
                value={form.zip_code}
                onChange={(e) => update("zip_code", e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Latitude (optional)"
                type="number"
                step="any"
                placeholder="40.7128"
                value={form.latitude}
                onChange={(e) => update("latitude", e.target.value)}
              />
              <Input
                label="Longitude (optional)"
                type="number"
                step="any"
                placeholder="-74.0060"
                value={form.longitude}
                onChange={(e) => update("longitude", e.target.value)}
              />
            </div>
          </div>
        )}

        {/* Step 3: Pricing & Rules */}
        {step === 3 && (
          <div className="space-y-4">
            <Input
              label="Nightly price ($)"
              type="number"
              min={1}
              placeholder="100"
              value={form.nightly_price}
              onChange={(e) => update("nightly_price", e.target.value)}
              error={errors.nightly_price}
            />

            {/* Hourly booking toggle */}
            <div className="rounded-lg border border-gray-200 p-4">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={form.enable_hourly}
                  onChange={(e) => update("enable_hourly", e.target.checked)}
                  className="rounded border-gray-300 text-rose-600 focus:ring-rose-500"
                />
                <div>
                  <p className="text-sm font-medium text-gray-900">Enable hourly bookings</p>
                  <p className="text-xs text-gray-500">Allow guests to book by the hour</p>
                </div>
              </label>
              {form.enable_hourly && (
                <div className="grid grid-cols-3 gap-3 mt-3">
                  <Input
                    label="Hourly rate ($)"
                    type="number"
                    min={1}
                    value={form.hourly_rate}
                    onChange={(e) => update("hourly_rate", e.target.value)}
                  />
                  <Input
                    label="Min hours"
                    type="number"
                    min={1}
                    value={form.min_hours}
                    onChange={(e) => update("min_hours", e.target.value)}
                  />
                  <Input
                    label="Max hours"
                    type="number"
                    min={1}
                    value={form.max_hours}
                    onChange={(e) => update("max_hours", e.target.value)}
                  />
                </div>
              )}
            </div>

            <Textarea
              label="House rules (optional)"
              placeholder="No smoking, quiet hours after 10pm..."
              rows={4}
              value={form.house_rules}
              onChange={(e) => update("house_rules", e.target.value)}
            />
          </div>
        )}

        {/* Step 4: Photos */}
        {step === 4 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Property Photos
              </label>
              <p className="text-xs text-gray-500 mb-3">
                Upload high-quality images. The first image (or the one you mark) will be the cover photo.
              </p>
              <label className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:border-rose-400 hover:bg-rose-50 transition">
                <svg
                  className="h-10 w-10 text-gray-400 mb-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M12 16v-8m0 0l-3 3m3-3l3 3M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1"
                  />
                </svg>
                <span className="text-sm text-gray-500">Click to upload images</span>
                <span className="text-xs text-gray-400 mt-1">JPG, PNG, WebP — max 10 MB each</span>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  className="hidden"
                  onChange={(e) => addImages(e.target.files)}
                />
              </label>
            </div>

            {images.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                {images.map((img, i) => (
                  <div
                    key={img.preview}
                    className={`relative group rounded-lg overflow-hidden border-2 ${
                      img.isPrimary ? "border-rose-500" : "border-gray-200"
                    }`}
                  >
                    <img
                      src={img.preview}
                      alt={`Upload ${i + 1}`}
                      className="w-full h-32 object-cover"
                    />
                    {img.isPrimary && (
                      <span className="absolute top-1.5 left-1.5 bg-rose-600 text-white text-xs font-medium px-2 py-0.5 rounded-full">
                        Cover
                      </span>
                    )}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
                      {!img.isPrimary && (
                        <button
                          type="button"
                          onClick={() => setPrimaryImage(i)}
                          className="bg-white text-gray-700 text-xs font-medium px-2 py-1 rounded-md hover:bg-gray-100"
                        >
                          Set Cover
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => removeImage(i)}
                        className="bg-white text-red-600 text-xs font-medium px-2 py-1 rounded-md hover:bg-red-50"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-4 border-t">
          {step > 1 ? (
            <Button variant="outline" onClick={() => setStep(step - 1)}>
              Back
            </Button>
          ) : (
            <div />
          )}
          {step < 4 ? (
            <Button onClick={() => validateStep(step) && setStep(step + 1)}>
              Continue
            </Button>
          ) : (
            <Button loading={loading} onClick={handleSubmit}>
              Publish Listing
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
