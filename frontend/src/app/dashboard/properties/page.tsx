/**
 * @module DashboardPropertiesPage
 * @description Host property listing management page with add/edit/delete actions.
 */
"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Button from "@/components/ui/button";
import { Badge, Spinner } from "@/components/ui/index";
import EmptyState from "@/components/ui/empty-state";
import { toast } from "@/components/ui/toast";
import { propertyApi } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { Property } from "@/types";

export default function DashboardPropertiesPage() {
  const { user } = useAuthStore();
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Wait for backendId — without it the search has no host_id filter and
    // returns all properties, causing a visible data jump when it arrives.
    if (!user?.backendId) return;
    const load = async () => {
      try {
        const res = await propertyApi.search({ host_id: user.backendId! });
        const data = res.data;
        setProperties(Array.isArray(data) ? data : data.items || []);
      } catch {
        setProperties([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user?.backendId]);

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this listing?")) return;
    try {
      await propertyApi.delete(id);
      setProperties((prev) => prev.filter((p) => p.id !== id));
      toast.success("Listing deleted");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">My Listings</h2>
        <Link href="/dashboard/properties/new">
          <Button>+ New Listing</Button>
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : properties.length === 0 ? (
        <EmptyState
          title="No listings yet"
          description="Create your first property listing to start hosting."
          action={
            <Link href="/dashboard/properties/new">
              <Button>Create Listing</Button>
            </Link>
          }
        />
      ) : (
        <div className="space-y-4">
          {properties.map((property) => (
            <div
              key={property.id}
              className="flex flex-col sm:flex-row gap-4 rounded-xl border border-gray-200 bg-white p-4"
            >
              {/* Thumbnail */}
              <div className="w-full sm:w-36 h-24 rounded-lg overflow-hidden bg-gray-100 shrink-0">
                <img
                  src={property.images?.[0]?.image_url || "/placeholder-property.svg"}
                  alt={property.title}
                  className="h-full w-full object-cover"
                />
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="font-semibold text-gray-900 truncate">
                      {property.title}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {property.city}
                    </p>
                  </div>
                  <Badge variant={property.is_active ? "success" : "default"}>
                    {property.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                  <span>₹{property.price_per_night}/night</span>
                  <span>Up to {property.max_guests} guests</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex sm:flex-col gap-2 sm:items-end shrink-0">
                <Link href={`/dashboard/properties/${property.id}/edit`}>
                  <Button variant="outline" size="sm">Edit</Button>
                </Link>
                <Link href={`/properties/${property.id}`}>
                  <Button variant="ghost" size="sm">View</Button>
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(property.id)}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
