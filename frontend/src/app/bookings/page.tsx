/**
 * @module BookingsPage
 * @description Guest bookings list page with tabs for upcoming, past, and cancelled bookings.
 */
"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Tabs from "@/components/ui/tabs";
import { Badge, Spinner } from "@/components/ui/index";
import EmptyState from "@/components/ui/empty-state";
import { bookingApi } from "@/lib/api";
import type { Booking } from "@/types";

const statusVariant: Record<string, "default" | "success" | "warning" | "error" | "info"> = {
  pending: "warning",
  confirmed: "success",
  completed: "default",
  cancelled: "error",
  rejected: "error",
};

export default function BookingsPage() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("upcoming");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await bookingApi.list();
        const data = res.data;
        setBookings(Array.isArray(data) ? data : data.items || []);
      } catch {
        setBookings([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const now = new Date();
  const filtered = bookings.filter((b) => {
    if (tab === "upcoming") return new Date(b.check_in) >= now && b.status !== "cancelled";
    if (tab === "past") return new Date(b.check_out) < now || b.status === "completed";
    if (tab === "cancelled") return b.status === "cancelled" || b.status === "rejected";
    return true;
  });

  const tabs = [
    { key: "upcoming", label: "Upcoming", count: bookings.filter((b) => new Date(b.check_in) >= now && b.status !== "cancelled").length },
    { key: "past", label: "Past", count: bookings.filter((b) => new Date(b.check_out) < now || b.status === "completed").length },
    { key: "cancelled", label: "Cancelled", count: bookings.filter((b) => b.status === "cancelled" || b.status === "rejected").length },
  ];

  return (
      <main className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">My Trips</h1>
        <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />

        <div className="mt-6">
          {loading ? (
            <div className="flex justify-center py-20"><Spinner size="lg" /></div>
          ) : filtered.length === 0 ? (
            <EmptyState
              title={tab === "upcoming" ? "No upcoming trips" : "No trips found"}
              description="When you book a stay, it will show up here."
              action={
                <Link
                  href="/properties"
                  className="text-sm font-medium text-rose-600 hover:text-rose-700"
                >
                  Start exploring →
                </Link>
              }
            />
          ) : (
            <div className="space-y-4">
              {filtered.map((booking) => (
                <Link
                  key={booking.id}
                  href={`/bookings/${booking.id}`}
                  className="block rounded-xl border border-gray-200 bg-white hover:shadow-md transition p-4 sm:p-6"
                >
                  <div className="flex flex-col sm:flex-row gap-4">
                    {/* Property image */}
                    <div className="w-full sm:w-40 h-28 rounded-lg overflow-hidden bg-gray-100 shrink-0">
                      <img
                        src="/placeholder-property.jpg"
                        alt="Property"
                        className="h-full w-full object-cover"
                      />
                    </div>

                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="font-semibold text-gray-900 truncate">
                            Booking #{booking.id.slice(0, 8)}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {booking.booking_type === "hourly" ? "Hourly" : "Nightly"} booking
                          </p>
                        </div>
                        <Badge variant={statusVariant[booking.status] || "default"}>
                          {booking.status}
                        </Badge>
                      </div>

                      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-600">
                        <span>
                          {new Date(booking.check_in).toLocaleDateString()} →{" "}
                          {new Date(booking.check_out).toLocaleDateString()}
                        </span>
                        <span className="font-semibold text-gray-900">
                          ₹{booking.total_price}
                        </span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
  );
}
