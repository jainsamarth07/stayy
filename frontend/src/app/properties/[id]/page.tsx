"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import ImageGallery from "@/components/property/image-gallery";
import StarRating from "@/components/property/star-rating";
import Button from "@/components/ui/button";
import { Avatar, Badge, Spinner } from "@/components/ui/index";
import { Textarea } from "@/components/ui/index";
import { toast } from "@/components/ui/toast";
import { propertyApi, bookingApi, reviewApi, messageApi, getApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { Property, Review } from "@/types";
import { Star, Share, Bookmark, Shield, Sparkles, MapPin, Check } from "lucide-react";

export default function PropertyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [property, setProperty] = useState<Property | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [bookingLoading, setBookingLoading] = useState(false);

  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState(1);

  const [showContact, setShowContact] = useState(false);
  const [contactMessage, setContactMessage] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [propRes, revsRes] = await Promise.all([
          propertyApi.getById(id),
          reviewApi.listByProperty(id).catch(() => ({ data: [] })),
        ]);
        setProperty(propRes.data);
        const revData = revsRes.data || revsRes;
        setReviews(Array.isArray(revData) ? revData : revData.items || []);
      } catch {
        toast.error("Property not found");
        router.push("/properties");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id, router]);

  const nights =
    checkIn && checkOut
      ? Math.max(
          1,
          Math.ceil(
            (new Date(checkOut).getTime() - new Date(checkIn).getTime()) /
              (1000 * 60 * 60 * 24)
          )
        )
      : 0;
  const totalPrice = property ? nights * property.price_per_night : 0;

  const handleBook = async () => {
    if (!isAuthenticated) {
      router.push("/auth/login");
      return;
    }
    if (!checkIn || !checkOut) {
      toast.error("Please select check-in and check-out dates");
      return;
    }
    if (property && guests > property.max_guests) {
      toast.error(`Maximum ${property.max_guests} guests allowed`);
      return;
    }
    if (new Date(checkIn) < new Date(new Date().toDateString())) {
      toast.error("Check-in date cannot be in the past");
      return;
    }
    setBookingLoading(true);
    try {
      await bookingApi.create({
        property_id: id,
        check_in: new Date(checkIn).toISOString(),
        check_out: new Date(checkOut).toISOString(),
        booking_type: "nightly",
      });
      toast.success("Booking request sent!");
      router.push("/bookings");
    } catch (err: unknown) {
      toast.error(getApiError(err));
    } finally {
      setBookingLoading(false);
    }
  };

  const handleContactHost = async () => {
    if (!isAuthenticated) {
      router.push("/auth/login");
      return;
    }
    if (!contactMessage.trim()) {
      toast.error("Please enter a message");
      return;
    }
    try {
      await messageApi.startConversation({
        property_id: id,
        message: contactMessage,
      });
      toast.success("Message sent to host!");
      setContactMessage("");
      setShowContact(false);
    } catch (err: unknown) {
      const msg = getApiError(err);
      if (msg.includes("already exists")) {
        toast.info("You already have a conversation about this property. Check your messages.");
        setShowContact(false);
      } else {
        toast.error(msg);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]"><Spinner size="lg" /></div>
    );
  }

  if (!property) return null;

  return (
    <main className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20 py-6">
      {/* Title section */}
      <div className="mb-5">
        <h1 className="text-[26px] font-semibold">{property.title}</h1>
        <div className="flex items-center justify-between mt-1">
          <div className="flex items-center gap-2 text-sm">
            {reviews.length > 0 && (
              <div className="flex items-center gap-1 font-semibold">
                <Star className="h-3.5 w-3.5 fill-current" />
                <span>{(reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1)}</span>
              </div>
            )}
            {reviews.length > 0 && (
              <>
                <span className="text-stone-500">·</span>
                <span className="underline font-semibold">{reviews.length} reviews</span>
              </>
            )}
            <span className="text-stone-500">·</span>
            <span className="underline font-semibold flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {property.city}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button className="flex items-center gap-1.5 text-sm font-semibold underline hover:bg-stone-50 rounded-lg px-2 py-1.5 transition">
              <Share className="h-4 w-4" />
              Share
            </button>
            <button className="flex items-center gap-1.5 text-sm font-semibold underline hover:bg-stone-50 rounded-lg px-2 py-1.5 transition">
              <Bookmark className="h-4 w-4" />
              Save
            </button>
          </div>
        </div>
      </div>

      {/* Image gallery */}
      <ImageGallery
        images={property.images?.map((img) => ({ url: img.image_url })) || []}
        title={property.title}
      />

      {/* Content grid */}
      <div className="mt-10 grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Left: Details */}
        <div className="lg:col-span-2 space-y-8">
          {/* Host info */}
          <div className="flex items-center justify-between pb-8 border-b">
            <div>
              <h2 className="text-[22px] font-semibold">
                Entire place hosted on StayNest
              </h2>
              <p className="text-stone-500 mt-1">
                {property.max_guests} guests
              </p>
            </div>
            <Avatar
              fallback="H"
              size="lg"
            />
          </div>

          {/* Highlights */}
          <div className="space-y-6 pb-8 border-b">
            {[
              { icon: Sparkles, title: "Dedicated workspace", desc: "A common area with wifi that's well-suited for working." },
              { icon: MapPin, title: "Great location", desc: "100% of recent guests gave the location a 5-star rating." },
              { icon: Shield, title: "Free cancellation", desc: "Full refund if plans change — no questions asked." },
            ].map((h) => (
              <div key={h.title} className="flex items-start gap-5">
                <h.icon className="h-6 w-6 mt-0.5 text-stone-700 shrink-0" strokeWidth={1.5} />
                <div>
                  <p className="font-semibold">{h.title}</p>
                  <p className="text-sm text-stone-500 mt-0.5">{h.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Booking protection */}
          <div className="pb-8 border-b">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="h-5 w-5 text-accent-600" />
              <span className="font-semibold text-stone-800">Booking Protection</span>
            </div>
            <p className="text-sm text-stone-500 leading-relaxed">
              Every booking includes free protection from Host cancellations, listing inaccuracies, and other issues like trouble checking in.
            </p>
          </div>

          {/* Description */}
          <div className="pb-8 border-b">
            <p className="text-neutral-700 whitespace-pre-line leading-7">
              {property.description}
            </p>
          </div>

          {/* Amenities */}
          {property.amenities && property.amenities.length > 0 && (
            <div className="pb-8 border-b">
              <h3 className="text-[22px] font-semibold mb-6">What this place offers</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {property.amenities.map((amenity) => (
                  <div key={amenity} className="flex items-center gap-4 py-1">
                    <Check className="h-5 w-5 text-stone-600" strokeWidth={1.5} />
                    <span className="text-stone-700">{amenity}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reviews */}
          <div>
            <div className="flex items-center gap-2 mb-6">
              <Star className="h-5 w-5 fill-current" />
              <h3 className="text-[22px] font-semibold">
                {reviews.length > 0 ? (
                  <>
                    {(reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1)}
                    {" · "}
                    {reviews.length} review{reviews.length !== 1 && "s"}
                  </>
                ) : (
                  "No reviews yet"
                )}
              </h3>
            </div>
            {reviews.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {reviews.map((review) => (
                  <div key={review.id}>
                    <div className="flex items-center gap-3 mb-3">
                      <Avatar fallback="G" size="sm" />
                      <div>
                        <p className="text-sm font-semibold">Guest</p>
                        <p className="text-xs text-stone-500">
                          {new Date(review.created_at).toLocaleDateString("en-US", {
                            month: "long",
                            year: "numeric",
                          })}
                        </p>
                      </div>
                    </div>
                    <StarRating rating={review.rating} size="sm" />
                    <p className="text-sm text-stone-600 mt-2 leading-relaxed line-clamp-4">{review.comment}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Booking card */}
        <div className="lg:col-span-1">
          <div className="sticky top-28 rounded-xl border shadow-xl p-6 space-y-5">
            <div className="flex items-baseline gap-1">
              <span className="text-[22px] font-semibold">
                ₹{property.price_per_night}
              </span>
              <span className="text-stone-500">night</span>
            </div>

            {property.hourly_config?.hourly_price && (
              <p className="text-sm text-stone-500">
                Also available hourly at ₹{property.hourly_config.hourly_price}/hr
              </p>
            )}

            {/* Dates & Guests */}
            <div className="border rounded-xl overflow-hidden">
              <div className="grid grid-cols-2 divide-x">
                <div className="p-3">
                  <label className="block text-[10px] font-bold uppercase tracking-wide">Check-in</label>
                  <input
                    type="date"
                    value={checkIn}
                    onChange={(e) => setCheckIn(e.target.value)}
                    min={new Date().toISOString().split("T")[0]}
                    className="w-full text-sm bg-transparent border-0 p-0 mt-0.5 focus:outline-none focus:ring-0"
                  />
                </div>
                <div className="p-3">
                  <label className="block text-[10px] font-bold uppercase tracking-wide">Checkout</label>
                  <input
                    type="date"
                    value={checkOut}
                    onChange={(e) => setCheckOut(e.target.value)}
                    min={checkIn}
                    className="w-full text-sm bg-transparent border-0 p-0 mt-0.5 focus:outline-none focus:ring-0"
                  />
                </div>
              </div>
              <div className="border-t p-3">
                <label className="block text-[10px] font-bold uppercase tracking-wide">Guests</label>
                <input
                  type="number"
                  min={1}
                  max={property.max_guests}
                  value={guests}
                  onChange={(e) => setGuests(parseInt(e.target.value) || 1)}
                  className="w-full text-sm bg-transparent border-0 p-0 mt-0.5 focus:outline-none focus:ring-0"
                />
              </div>
            </div>

            {/* Reserve button */}
            <Button
              fullWidth
              onClick={handleBook}
              loading={bookingLoading}
              size="lg"
              className="bg-primary-500 hover:bg-primary-600 rounded-xl text-base"
            >
              {nights > 0 ? "Reserve" : "Check availability"}
            </Button>

            <p className="text-center text-xs text-stone-500">You won&apos;t be charged yet</p>

            {/* Price breakdown */}
            {nights > 0 && (
              <div className="space-y-3 pt-4 border-t">
                <div className="flex justify-between text-sm">
                  <span className="underline text-stone-700">
                    ₹{property.price_per_night} x {nights} night{nights !== 1 ? "s" : ""}
                  </span>
                  <span>₹{totalPrice}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="underline text-stone-700">Cleaning fee</span>
                  <span>₹0</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="underline text-stone-700">Service fee</span>
                  <span>₹0</span>
                </div>
                <div className="flex justify-between font-semibold pt-3 border-t text-base">
                  <span>Total</span>
                  <span>₹{totalPrice}</span>
                </div>
              </div>
            )}

            {/* Contact Host */}
            <button
              onClick={() => setShowContact(!showContact)}
              className="w-full text-center text-sm text-stone-600 hover:text-stone-800 font-semibold underline transition"
            >
              {showContact ? "Cancel" : "Contact Host"}
            </button>

            {showContact && (
              <div className="space-y-3 pt-3 border-t">
                <Textarea
                  label="Message to host"
                  placeholder="Ask a question about this property..."
                  rows={3}
                  value={contactMessage}
                  onChange={(e) => setContactMessage(e.target.value)}
                />
                <Button fullWidth variant="outline" onClick={handleContactHost}>
                  Send Message
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
