/**
 * @module DashboardBookingsPage
 * @description Host booking management page with filtering by status and inline action buttons.
 */
"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Button from "@/components/ui/button";
import { Badge, Spinner } from "@/components/ui/index";
import EmptyState from "@/components/ui/empty-state";
import { toast } from "@/components/ui/toast";
import { bookingApi, getApiError } from "@/lib/api";
import Tabs from "@/components/ui/tabs";
import type { Booking } from "@/types";

const statusColors: Record<string, "default" | "success" | "warning" | "error" | "info"> = {
  pending: "warning",
  confirmed: "success",
  checked_in: "info",
  completed: "default",
  cancelled: "error",
  rejected: "error",
};

export default function DashboardBookingsPage() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("pending");

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

  const filtered = bookings.filter((b) => {
    if (tab === "pending") return b.status === "pending";
    if (tab === "confirmed") return b.status === "confirmed" || b.status === "checked_in";
    if (tab === "completed") return b.status === "completed";
    if (tab === "cancelled") return b.status === "cancelled" || b.status === "rejected";
    return true;
  });

  const tabs = [
    { key: "pending", label: "Pending", count: bookings.filter((b) => b.status === "pending").length },
    { key: "confirmed", label: "Active", count: bookings.filter((b) => b.status === "confirmed" || b.status === "checked_in").length },
    { key: "completed", label: "Completed", count: bookings.filter((b) => b.status === "completed").length },
    { key: "cancelled", label: "Cancelled", count: bookings.filter((b) => b.status === "cancelled" || b.status === "rejected").length },
  ];

  const handleAction = async (id: string, action: "confirm" | "reject" | "complete") => {
    const statusMap = { confirm: "confirmed" as const, reject: "rejected" as const, complete: "completed" as const };
    try {
      await bookingApi.updateStatus(id, statusMap[action]);
      toast.success(`Booking ${statusMap[action]}!`);
      setBookings((prev) =>
        prev.map((b) =>
          b.id === id ? { ...b, status: statusMap[action] } : b
        )
      );
    } catch (err: unknown) {
      toast.error(getApiError(err));
    }
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-6">Guest Bookings</h2>
      <Tabs tabs={tabs} activeTab={tab} onChange={setTab} />

      <div className="mt-6">
        {loading ? (
          <div className="flex justify-center py-20"><Spinner size="lg" /></div>
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No bookings"
            description={`No ${tab} bookings at the moment.`}
          />
        ) : (
          <div className="space-y-4">
            {filtered.map((booking) => (
              <Link
                key={booking.id}
                href={`/bookings/${booking.id}`}
                className="block rounded-xl border border-gray-200 bg-white p-4 sm:p-6 hover:shadow-md transition"
              >
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          Booking #{booking.id.slice(0, 8)}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {booking.booking_type === "hourly" ? "Hourly" : "Nightly"} booking
                        </p>
                      </div>
                      <Badge variant={statusColors[booking.status]}>
                        {booking.status}
                      </Badge>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-sm text-gray-600">
                      <span>
                        {new Date(booking.check_in).toLocaleDateString()} →{" "}
                        {new Date(booking.check_out).toLocaleDateString()}
                      </span>
                      <span className="font-semibold">₹{booking.total_price}</span>
                    </div>
                  </div>

                  {booking.status === "pending" && (
                    <div className="flex gap-2 sm:flex-col shrink-0" onClick={(e) => e.preventDefault()}>
                      <Button
                        size="sm"
                        onClick={(e) => { e.preventDefault(); handleAction(booking.id, "confirm"); }}
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        onClick={(e) => { e.preventDefault(); handleAction(booking.id, "reject"); }}
                      >
                        Reject
                      </Button>
                    </div>
                  )}
                  {booking.status === "confirmed" && (
                    <div className="flex gap-2 sm:flex-col shrink-0" onClick={(e) => e.preventDefault()}>
                      <Button
                        size="sm"
                        onClick={(e) => { e.preventDefault(); handleAction(booking.id, "complete"); }}
                      >
                        Mark Complete
                      </Button>
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
