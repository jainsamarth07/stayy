/**
 * @module DashboardReviewsPage
 * @description Host reviews page displaying guest reviews for all hosted properties.
 */
"use client";

import React, { useEffect, useState } from "react";
import { Spinner } from "@/components/ui/index";
import StarRating from "@/components/property/star-rating";
import { Avatar } from "@/components/ui/index";
import EmptyState from "@/components/ui/empty-state";
import { reviewApi } from "@/lib/api";
import type { Review } from "@/types";

export default function DashboardReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await reviewApi.hostReviews();
        const data = res.data;
        setReviews(Array.isArray(data) ? data : data.items || []);
      } catch {
        setReviews([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const avgRating =
    reviews.length > 0
      ? reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length
      : 0;

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-2">Guest Reviews</h2>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : reviews.length === 0 ? (
        <EmptyState
          title="No reviews yet"
          description="Reviews from guests will appear here after they complete their stay."
        />
      ) : (
        <>
          {/* Summary */}
          <div className="flex items-center gap-4 mb-6 p-4 rounded-xl bg-gray-50">
            <div className="text-center">
              <p className="text-3xl font-bold text-gray-900">{avgRating.toFixed(1)}</p>
              <StarRating rating={Math.round(avgRating)} size="sm" />
            </div>
            <p className="text-sm text-gray-500">
              Based on {reviews.length} review{reviews.length !== 1 ? "s" : ""}
            </p>
          </div>

          {/* Review list */}
          <div className="space-y-4">
            {reviews.map((review) => (
              <div key={review.id} className="rounded-xl border border-gray-200 bg-white p-5">
                <div className="flex items-center gap-3 mb-3">
                  <Avatar
                    fallback="G"
                    size="md"
                  />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Guest review
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(review.created_at).toLocaleDateString("en-US", {
                        month: "long",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </p>
                  </div>
                </div>
                <StarRating rating={review.rating} size="sm" />
                <p className="text-sm text-gray-600 mt-2">{review.comment}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
