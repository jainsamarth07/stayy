/**
 * @module MembershipPage
 * @description Host membership tier management page showing current plan, tier comparison, and upgrade flow.
 */
"use client";

import React, { useEffect, useState } from "react";
import Button from "@/components/ui/button";
import { Badge, Card, Spinner } from "@/components/ui/index";
import { toast } from "@/components/ui/toast";
import { membershipApi } from "@/lib/api";

interface MembershipPlan {
  tier: string;
  name: string;
  price: number;
  features: string[];
  listing_limit: number | "Unlimited";
  popular?: boolean;
}

const plans: MembershipPlan[] = [
  {
    tier: "basic",
    name: "Basic",
    price: 2499,
    listing_limit: 5,
    features: [
      "Up to 5 property listings",
      "Standard search placement",
      "Email support",
      "Basic analytics",
      "0% commission — always",
    ],
  },
  {
    tier: "pro",
    name: "Professional",
    price: 6499,
    listing_limit: 25,
    popular: true,
    features: [
      "Up to 25 property listings",
      "Priority search placement",
      "Priority support",
      "Advanced analytics & reports",
      "Hourly bookings enabled",
      "Custom booking rules",
      "0% commission — always",
    ],
  },
  {
    tier: "premium",
    name: "Premium",
    price: 16499,
    listing_limit: "Unlimited",
    features: [
      "Unlimited property listings",
      "Top search placement",
      "Dedicated account manager",
      "Full analytics suite",
      "API access",
      "Multi-calendar sync",
      "White-label booking page",
      "0% commission — always",
    ],
  },
];

export default function MembershipPage() {
  const [currentPlan, setCurrentPlan] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await membershipApi.getCurrent();
        setCurrentPlan(res?.data?.plan_type || null);
      } catch {
        setCurrentPlan(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleSubscribe = async (tier: string) => {
    setActionLoading(tier);
    try {
      await membershipApi.subscribe(tier, "placeholder_token");
      setCurrentPlan(tier);
      toast.success(
        currentPlan
          ? `Switched to ${tier} plan!`
          : `Subscribed to ${tier} plan!`
      );
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const detail = axiosErr?.response?.data?.detail;
      toast.error(detail || (err instanceof Error ? err.message : "Subscription failed"));
    } finally {
      setActionLoading(null);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel your membership?")) return;
    try {
      await membershipApi.cancel();
      setCurrentPlan(null);
      toast.success("Membership cancelled");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Cancel failed");
    }
  };

  if (loading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-xl font-bold text-gray-900">Membership Plan</h2>
        <p className="text-sm text-gray-500 mt-1">
          Choose the plan that fits your hosting needs. Zero commissions on every plan.
        </p>
      </div>

      {currentPlan && (
        <div className="rounded-xl bg-green-50 border border-green-200 p-4 mb-6 flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-green-800">
              Current plan: <span className="font-bold capitalize">{currentPlan}</span>
            </p>
            <p className="text-xs text-green-600 mt-0.5">Your membership is active</p>
          </div>
          <Button variant="outline" size="sm" onClick={handleCancel}>
            Cancel Plan
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => {
          const isCurrent = currentPlan === plan.tier;
          return (
            <div
              key={plan.tier}
              className={`relative rounded-xl border-2 p-6 ${
                plan.popular
                  ? "border-primary-500 shadow-lg"
                  : isCurrent
                  ? "border-green-500"
                  : "border-gray-200"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge variant="error">Most Popular</Badge>
                </div>
              )}

              <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="text-3xl font-bold text-gray-900">₹{plan.price}</span>
                <span className="text-gray-500">/month</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {plan.listing_limit === "Unlimited"
                  ? "Unlimited listings"
                  : `Up to ${plan.listing_limit} listings`}
              </p>

              <ul className="mt-6 space-y-2">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-green-500 shrink-0 mt-0.5">✓</span>
                    {f}
                  </li>
                ))}
              </ul>

              <div className="mt-6">
                {isCurrent ? (
                  <Button fullWidth variant="outline" disabled>
                    Current Plan
                  </Button>
                ) : (
                  <Button
                    fullWidth
                    variant={plan.popular ? "primary" : "outline"}
                    loading={actionLoading === plan.tier}
                    onClick={() => handleSubscribe(plan.tier)}
                  >
                    {currentPlan ? "Switch Plan" : "Subscribe"}
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8 text-center text-sm text-gray-500">
        All plans include <strong>0% commission</strong> on all bookings.
        You keep 100% of your revenue.
      </div>
    </div>
  );
}
