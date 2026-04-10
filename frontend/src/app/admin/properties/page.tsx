/**
 * @module AdminPropertiesPage
 * @description Admin property moderation page for reviewing, approving, and removing listings.
 */
"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import Button from "@/components/ui/button";
import { Badge, Spinner } from "@/components/ui/index";
import { toast } from "@/components/ui/toast";
import { adminApi, getApiError } from "@/lib/api";
import type { Property } from "@/types";

export default function AdminPropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const res = await adminApi.listProperties();
        const data = res.data;
        setProperties(Array.isArray(data) ? data : data.items || []);
      } catch {
        setProperties([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filtered = useMemo(() => {
    if (!search.trim()) return properties;
    const q = search.toLowerCase();
    return properties.filter(
      (p) =>
        p.title?.toLowerCase().includes(q) ||
        p.city?.toLowerCase().includes(q) ||
        p.host_name?.toLowerCase().includes(q)
    );
  }, [properties, search]);

  const handleToggleActive = async (id: string, currentlyActive: boolean) => {
    try {
      await adminApi.togglePropertyStatus(id);
      setProperties((prev) =>
        prev.map((p) => (p.id === id ? { ...p, is_active: !currentlyActive } : p))
      );
      toast.success(currentlyActive ? "Property deactivated" : "Property activated");
    } catch (err: unknown) {
      toast.error(getApiError(err));
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Properties</h2>
        <input
          type="text"
          placeholder="Search properties..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-200"
        />
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Property</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Host</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Status</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Price/Night</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-10 text-sm text-gray-500">
                    No properties found
                  </td>
                </tr>
              ) : (
                filtered.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-14 rounded bg-gray-200 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{p.title}</p>
                          <p className="text-xs text-gray-500">{p.city}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{p.host_name || "—"}</td>
                    <td className="px-4 py-3">
                      <Badge variant={p.is_active ? "success" : "default"}>{p.is_active ? "active" : "inactive"}</Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">₹{p.price_per_night}</td>
                    <td className="px-4 py-3 flex gap-2">
                      <Link href={`/properties/${p.id}`}>
                        <Button variant="ghost" size="sm">View</Button>
                      </Link>
                      <Button
                        variant={p.is_active ? "danger" : "outline"}
                        size="sm"
                        onClick={() => handleToggleActive(p.id, !!p.is_active)}
                      >
                        {p.is_active ? "Deactivate" : "Activate"}
                      </Button>
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
