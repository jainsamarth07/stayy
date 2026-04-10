/**
 * @module AdminMembershipsPage
 * @description Admin membership management page for monitoring subscriptions and revenue.
 */
"use client";

import React, { useEffect, useState } from "react";
import Button from "@/components/ui/button";
import { Badge, Spinner } from "@/components/ui/index";
import { adminApi } from "@/lib/api";

interface MembershipRow {
  id: string;
  user_name: string;
  email: string;
  plan: "basic" | "pro" | "premium";
  status: "active" | "cancelled" | "expired";
  started_at: string;
  expires_at: string;
}

const planColor: Record<string, "default" | "success" | "info" | "error"> = {
  basic: "default",
  pro: "info",
  premium: "success",
};

const statusColor: Record<string, "default" | "success" | "info" | "error"> = {
  active: "success",
  cancelled: "error",
  expired: "default",
};

export default function AdminMembershipsPage() {
  const [memberships, setMemberships] = useState<MembershipRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await adminApi.listMemberships();
        const data = res.data;
        setMemberships(Array.isArray(data) ? data : data.items || []);
      } catch {
        setMemberships([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-6">Memberships</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {[
          {
            label: "Active Subscriptions",
            value: String(memberships.filter((m) => m.status === "active").length),
            color: "text-green-600",
          },
          {
            label: "Monthly Revenue",
            value: `₹${memberships.filter((m) => m.status === "active").reduce((s, m) => s + Number((m as Record<string, unknown>).amount || 0), 0).toLocaleString()}`,
            color: "text-blue-600",
          },
          {
            label: "Expired / Cancelled",
            value: String(memberships.filter((m) => m.status !== "active").length),
            color: "text-amber-600",
          },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-sm text-gray-500">{s.label}</p>
            <p className={`text-2xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Host</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Plan</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Status</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Started</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Expires</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {memberships.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-sm text-gray-500">
                    No memberships found
                  </td>
                </tr>
              ) : (
                memberships.map((m) => (
                  <tr key={m.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <p className="text-sm font-medium text-gray-900">{m.user_name}</p>
                      <p className="text-xs text-gray-500">{m.email}</p>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={planColor[m.plan]}>{m.plan}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={statusColor[m.status]}>{m.status}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{m.started_at}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{m.expires_at}</td>
                    <td className="px-4 py-3">
                      <Button variant="ghost" size="sm">View</Button>
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
