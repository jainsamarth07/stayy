/**
 * @module DashboardPage
 * @description Host dashboard overview showing key metrics, recent bookings, and quick actions.
 */
"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/index";
import { Spinner } from "@/components/ui/index";
import Button from "@/components/ui/button";
import { propertyApi, bookingApi, reviewApi } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

interface DashboardStats {
  totalProperties: number;
  activeBookings: number;
  totalEarnings: number;
  averageRating: number;
  occupancyRate: number;
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    totalProperties: 0,
    activeBookings: 0,
    totalEarnings: 0,
    averageRating: 0,
    occupancyRate: 0,
  });

  useEffect(() => {
    // Wait for backendId before fetching — fetching without it returns all
    // properties (no host_id filter) causing stats to flash incorrect values.
    if (!user?.backendId) return;
    const load = async () => {
      try {
        const [propertiesRes, bookingsRes, reviewsRes] = await Promise.all([
          propertyApi.search({ host_id: user.backendId! }).catch(() => ({ data: [] })),
          bookingApi.list().catch(() => ({ data: [] })),
          reviewApi.hostReviews().catch(() => ({ data: [] })),
        ]);
        const propList = Array.isArray(propertiesRes.data) ? propertiesRes.data : propertiesRes.data.items || [];
        const bookList = Array.isArray(bookingsRes.data) ? bookingsRes.data : bookingsRes.data.items || [];
        const revList = Array.isArray(reviewsRes.data) ? reviewsRes.data : reviewsRes.data.items || [];
        const active = bookList.filter(
          (b: { status: string }) => b.status === "confirmed" || b.status === "checked_in"
        );
        const earnings = bookList
          .filter((b: { status: string }) => b.status === "completed")
          .reduce((sum: number, b: { total_price: number }) => sum + (b.total_price || 0), 0);
        const avgRating =
          revList.length > 0
            ? revList.reduce((sum: number, r: { rating: number }) => sum + r.rating, 0) / revList.length
            : 0;

        setStats({
          totalProperties: propList.length,
          activeBookings: active.length,
          totalEarnings: earnings,
          averageRating: avgRating,
          occupancyRate: 0,
        });
      } catch {
        // use defaults
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user?.backendId]);

  if (loading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  }

  const statCards = [
    { label: "Total Listings", value: stats.totalProperties, color: "bg-blue-50 text-blue-700" },
    { label: "Active Bookings", value: stats.activeBookings, color: "bg-green-50 text-green-700" },
    { label: "Total Earnings", value: `₹${stats.totalEarnings.toLocaleString()}`, color: "bg-rose-50 text-rose-700" },
    { label: "Avg Rating", value: stats.averageRating > 0 ? stats.averageRating.toFixed(1) : "N/A", color: "bg-yellow-50 text-yellow-700" },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.full_name}!
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Here&apos;s your hosting overview
          </p>
        </div>
        <Link href="/dashboard/properties/new">
          <Button>+ Add Listing</Button>
        </Link>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat) => (
          <Card key={stat.label} className="p-5">
            <p className="text-sm text-gray-500">{stat.label}</p>
            <p className={`text-2xl font-bold mt-1 ${stat.color.split(" ")[1]}`}>
              {stat.value}
            </p>
          </Card>
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Your Listings</h3>
          <p className="text-sm text-gray-500 mb-4">
            Manage your properties, update pricing and availability.
          </p>
          <Link href="/dashboard/properties">
            <Button variant="outline" size="sm">View Listings →</Button>
          </Link>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Guest Bookings</h3>
          <p className="text-sm text-gray-500 mb-4">
            Review and manage incoming booking requests.
          </p>
          <Link href="/dashboard/bookings">
            <Button variant="outline" size="sm">View Bookings →</Button>
          </Link>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Membership Plan</h3>
          <p className="text-sm text-gray-500 mb-4">
            Manage your subscription — zero commissions, always.
          </p>
          <Link href="/dashboard/membership">
            <Button variant="outline" size="sm">Manage Plan →</Button>
          </Link>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Messages</h3>
          <p className="text-sm text-gray-500 mb-4">
            Respond to guest inquiries and stay in touch.
          </p>
          <Link href="/messages">
            <Button variant="outline" size="sm">Open Messages →</Button>
          </Link>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Reviews</h3>
          <p className="text-sm text-gray-500 mb-4">
            See what guests are saying about your properties.
          </p>
          <Link href="/dashboard/reviews">
            <Button variant="outline" size="sm">View Reviews →</Button>
          </Link>
        </Card>
      </div>
    </div>
  );
}
