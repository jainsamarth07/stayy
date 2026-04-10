/**
 * @module AdminBookingsPage
 * @description Admin booking oversight page for viewing all platform bookings and intervening if needed.
 */
"use client";

import React, { useEffect, useState } from "react";
import Button from "@/components/ui/button";
import { Badge, Spinner } from "@/components/ui/index";
import { adminApi } from "@/lib/api";
import type { Booking } from "@/types";

export default function AdminBookingsPage() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await adminApi.listBookings();
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

  const statusColor: Record<string, "default" | "success" | "info" | "error"> = {
    pending: "info",
    confirmed: "success",
    cancelled: "error",
    completed: "default",
  };

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-6">Bookings</h2>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Booking ID</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Property</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Guest</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Dates</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Status</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {bookings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-sm text-gray-500">
                    No bookings found
                  </td>
                </tr>
              ) : (
                bookings.map((b) => (
                  <tr key={b.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-600 font-mono">
                      #{b.id.slice(0, 8)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{b.property_title || b.property_id}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{b.guest_name || b.guest_id}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(b.check_in).toLocaleDateString()} → {new Date(b.check_out).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusColor[b.status] || "default"}>{b.status}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      ₹{b.total_price}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
