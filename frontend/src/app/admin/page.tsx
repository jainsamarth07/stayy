/**
 * @module AdminDashboardPage
 * @description Admin overview dashboard showing platform-wide KPIs, charts, and recent activity.
 */
"use client";

import React, { useEffect, useState } from "react";
import { Card, Spinner } from "@/components/ui/index";
import { adminApi } from "@/lib/api";

interface AdminStats {
  totalUsers: number;
  totalProperties: number;
  totalBookings: number;
  activeMembers: number;
  monthlyRevenue: number;
  platformGrowth: number;
}

export default function AdminDashboardPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<AdminStats>({
    totalUsers: 0,
    totalProperties: 0,
    totalBookings: 0,
    activeMembers: 0,
    monthlyRevenue: 0,
    platformGrowth: 0,
  });

  useEffect(() => {
    // Fetch admin stats
    const load = async () => {
      try {
        const res = await adminApi.dashboard();
        const data = res.data;
        setStats({
          totalUsers: data.total_users ?? 0,
          totalProperties: data.total_properties ?? 0,
          totalBookings: data.total_bookings ?? 0,
          activeMembers: data.active_members ?? 0,
          monthlyRevenue: data.monthly_revenue ?? 0,
          platformGrowth: data.platform_growth ?? 0,
        });
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  }

  const cards = [
    { label: "Total Users", value: stats.totalUsers.toLocaleString(), color: "text-blue-600" },
    { label: "Properties", value: stats.totalProperties.toLocaleString(), color: "text-green-600" },
    { label: "Total Bookings", value: stats.totalBookings.toLocaleString(), color: "text-purple-600" },
    { label: "Active Members", value: stats.activeMembers.toLocaleString(), color: "text-primary-600" },
    { label: "Monthly Revenue", value: `₹${stats.monthlyRevenue.toLocaleString()}`, color: "text-emerald-600" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {cards.map((card) => (
          <Card key={card.label} className="p-5">
            <p className="text-sm text-gray-500">{card.label}</p>
            <p className={`text-2xl font-bold mt-1 ${card.color}`}>{card.value}</p>
          </Card>
        ))}
      </div>

      {/* Quick admin actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Quick Links</h3>
          <div className="space-y-3">
            {[
              { label: "Manage Users", href: "/admin/users" },
              { label: "Manage Properties", href: "/admin/properties" },
              { label: "Manage Bookings", href: "/admin/bookings" },
              { label: "Manage Memberships", href: "/admin/memberships" },
            ].map((link) => (
              <a key={link.href} href={link.href} className="flex items-center gap-3 text-sm text-primary-600 hover:text-primary-800 font-medium">
                <div className="h-2 w-2 rounded-full bg-primary-400 shrink-0" />
                {link.label}
              </a>
            ))}
          </div>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold text-gray-900 mb-2">Membership Plans</h3>
          <div className="space-y-3">
            {[
              { plan: "Basic (₹2,499/mo)", listings: "Up to 5 listings" },
              { plan: "Pro (₹6,499/mo)", listings: "Up to 25 listings" },
              { plan: "Premium (₹16,499/mo)", listings: "Unlimited listings" },
            ].map((item) => (
              <div key={item.plan} className="flex items-center justify-between text-sm">
                <span className="text-gray-600">{item.plan}</span>
                <span className="text-gray-400">{item.listings}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
