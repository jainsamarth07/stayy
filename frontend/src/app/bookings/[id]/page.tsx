/**
 * @module BookingDetailPage
 * @description Booking detail page showing reservation info, property summary, and action buttons.
 */
"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Button from "@/components/ui/button";
import { Badge, Spinner } from "@/components/ui/index";
import { Textarea } from "@/components/ui/index";
import StarRating from "@/components/property/star-rating";
import { toast } from "@/components/ui/toast";
import { bookingApi, reviewApi, messageApi, propertyApi, getApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { Booking, Property } from "@/types";

const statusColors: Record<string, "default" | "success" | "warning" | "error" | "info"> = {
  pending: "warning",
  confirmed: "success",
  checked_in: "info",
  completed: "default",
  cancelled: "error",
  rejected: "error",
};

export default function BookingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuthStore();
  const [booking, setBooking] = useState<Booking | null>(null);
  const [property, setProperty] = useState<Property | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReview, setShowReview] = useState(false);
  const [reviewRating, setReviewRating] = useState(0);
  const [reviewComment, setReviewComment] = useState("");
  const [messageText, setMessageText] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await bookingApi.getById(id);
        setBooking(res.data);
        // Fetch property details
        try {
          const propRes = await propertyApi.getById(res.data.property_id);
          setProperty(propRes.data);
        } catch {
          // Property fetch is non-critical
        }
      } catch {
        toast.error("Booking not found");
        router.push("/bookings");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id, router]);

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel this booking?")) return;
    try {
      await bookingApi.updateStatus(id, "cancelled");
      toast.success("Booking cancelled");
      setBooking((prev) => prev && { ...prev, status: "cancelled" });
    } catch (err: unknown) {
      toast.error(getApiError(err));
    }
  };

  const handleReview = async () => {
    if (reviewRating === 0) {
      toast.error("Please select a rating");
      return;
    }
    try {
      await reviewApi.create({
        booking_id: id,
        rating: reviewRating,
        comment: reviewComment || undefined,
      });
      toast.success("Review submitted!");
      setShowReview(false);
    } catch (err: unknown) {
      toast.error(getApiError(err));
    }
  };

  const handleMessage = async () => {
    if (!messageText.trim()) return;
    try {
      await messageApi.startConversation({
        property_id: booking!.property_id,
        message: messageText,
      });
      toast.success("Message sent to host");
      setMessageText("");
    } catch (err: unknown) {
      const msg = getApiError(err);
      if (msg.includes("already exists")) {
        toast.info("You already have a conversation. Check your messages.");
      } else {
        toast.error(msg);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20"><Spinner size="lg" /></div>
    );
  }

  if (!booking) return null;

  const nights = Math.ceil(
    (new Date(booking.check_out).getTime() - new Date(booking.check_in).getTime()) /
      (1000 * 60 * 60 * 24)
  );

  return (
      <main className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <button
              onClick={() => router.push("/bookings")}
              className="text-sm text-gray-500 hover:text-gray-700 mb-2 flex items-center gap-1"
            >
              ← Back to trips
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              Booking Details
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Booking #{booking.id.slice(0, 8)}
            </p>
          </div>
          <Badge variant={statusColors[booking.status] || "default"}>
            {booking.status}
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Booking info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Property card */}
            <div className="rounded-xl border border-gray-200 overflow-hidden">
              <div className="h-48 bg-gray-100">
                <img
                  src={property?.images?.[0]?.image_url || "/placeholder-property.svg"}
                  alt={property?.title || "Property"}
                  className="h-full w-full object-cover"
                />
              </div>
              <div className="p-4">
                <h3 className="font-semibold text-gray-900">{property?.title || `Property #${booking.property_id.slice(0, 8)}`}</h3>
                <p className="text-sm text-gray-500">
                  {property?.city ? `${property.city} · ` : ""}
                  {booking.booking_type === "hourly" ? "Hourly" : "Nightly"} booking
                </p>
              </div>
            </div>

            {/* Dates & guests */}
            <div className="rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Trip Details</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider">Check-in</p>
                  <p className="text-sm font-medium text-gray-900 mt-1">
                    {new Date(booking.check_in).toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider">Check-out</p>
                  <p className="text-sm font-medium text-gray-900 mt-1">
                    {new Date(booking.check_out).toLocaleDateString("en-US", {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 uppercase tracking-wider">Duration</p>
                  <p className="text-sm font-medium text-gray-900 mt-1">
                    {nights} night{nights !== 1 ? "s" : ""}
                  </p>
                </div>
              </div>
            </div>

            {/* Contact host */}
            <div className="rounded-xl border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-3">Message Host</h3>
              <div className="flex gap-2">
                <Textarea
                  placeholder="Ask the host a question..."
                  rows={2}
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                />
                <Button onClick={handleMessage} className="self-end">
                  Send
                </Button>
              </div>
            </div>

            {/* Review (for completed bookings) */}
            {booking.status === "completed" && (
              <div className="rounded-xl border border-gray-200 p-6">
                <h3 className="font-semibold text-gray-900 mb-3">Leave a Review</h3>
                {showReview ? (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm text-gray-600 mb-1">Rating</label>
                      <StarRating rating={reviewRating} interactive onRate={setReviewRating} />
                    </div>
                    <Textarea
                      label="Your review"
                      placeholder="How was your stay?"
                      rows={4}
                      value={reviewComment}
                      onChange={(e) => setReviewComment(e.target.value)}
                    />
                    <div className="flex gap-2">
                      <Button onClick={handleReview}>Submit Review</Button>
                      <Button variant="outline" onClick={() => setShowReview(false)}>Cancel</Button>
                    </div>
                  </div>
                ) : (
                  <Button variant="outline" onClick={() => setShowReview(true)}>
                    Write a Review
                  </Button>
                )}
              </div>
            )}
          </div>

          {/* Right: Payment summary */}
          <div>
            <div className="sticky top-24 rounded-xl border border-gray-200 p-6 space-y-4">
              <h3 className="font-semibold text-gray-900">Price Details</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Nightly rate × {nights}</span>
                  <span>₹{booking.total_price}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Service fee</span>
                  <span className="text-green-600">₹0 (no commissions!)</span>
                </div>
                <hr />
                <div className="flex justify-between font-semibold text-base">
                  <span>Total</span>
                  <span>₹{booking.total_price}</span>
                </div>
              </div>

              {/* Actions */}
              {/* Guest actions */}
              {(booking.status === "pending" || booking.status === "confirmed") &&
                booking.guest_id === user?.backendId && (
                <Button
                  fullWidth
                  variant="danger"
                  onClick={handleCancel}
                >
                  Cancel Booking
                </Button>
              )}

              {/* Host actions */}
              {booking.host_id === user?.backendId && booking.status === "pending" && (
                <div className="space-y-2">
                  <Button
                    fullWidth
                    onClick={async () => {
                      try {
                        await bookingApi.updateStatus(id, "confirmed");
                        toast.success("Booking confirmed!");
                        setBooking((prev) => prev && { ...prev, status: "confirmed" });
                      } catch (err: unknown) {
                        toast.error(getApiError(err));
                      }
                    }}
                  >
                    Confirm Booking
                  </Button>
                  <Button
                    fullWidth
                    variant="danger"
                    onClick={async () => {
                      try {
                        await bookingApi.updateStatus(id, "rejected");
                        toast.success("Booking rejected");
                        setBooking((prev) => prev && { ...prev, status: "rejected" });
                      } catch (err: unknown) {
                        toast.error(getApiError(err));
                      }
                    }}
                  >
                    Reject Booking
                  </Button>
                </div>
              )}
              {booking.host_id === user?.backendId && booking.status === "confirmed" && (
                <div className="space-y-2">
                  <Button
                    fullWidth
                    onClick={async () => {
                      try {
                        await bookingApi.updateStatus(id, "completed");
                        toast.success("Booking marked as completed!");
                        setBooking((prev) => prev && { ...prev, status: "completed" });
                      } catch (err: unknown) {
                        toast.error(getApiError(err));
                      }
                    }}
                  >
                    Mark as Completed
                  </Button>
                  <Button
                    fullWidth
                    variant="danger"
                    onClick={handleCancel}
                  >
                    Cancel Booking
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
  );
}
