"use client";

import React, { useState } from "react";
import Link from "next/link";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { toast } from "@/components/ui/toast";
import { authClient } from "@/lib/auth-client";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !/\S+@\S+\.\S+/.test(email)) {
      toast.error("Please enter a valid email");
      return;
    }
    setLoading(true);
    const { error } = await authClient.requestPasswordReset({
      email,
      redirectTo: "/auth/reset-password",
    });
    setLoading(false);

    if (error) {
      toast.error(error.message || "Failed to send reset email");
      return;
    }
    setSent(true);
    toast.success("Reset email sent!");
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        <div className="flex items-center justify-center mb-6">
          <svg viewBox="0 0 32 32" className="h-10 w-10 text-primary-500 fill-current">
            <path d="M16 3C16 3 6 11 6 18c0 5.523 4.477 10 10 10s10-4.477 10-10C26 11 16 3 16 3z" opacity="0.2"/>
            <path d="M16 2c-.4 0-.8.15-1.1.43C13.5 3.8 5 11.5 5 18c0 6.075 4.925 11 11 11s11-4.925 11-11c0-6.5-8.5-14.2-9.9-15.57A1.5 1.5 0 0016 2zm0 3.4C18.2 7.5 25 13.6 25 18c0 4.97-4.03 9-9 9s-9-4.03-9-9c0-4.4 6.8-10.5 9-12.6z"/>
            <ellipse cx="16" cy="20" rx="4" ry="3" opacity="0.35"/>
          </svg>
        </div>

        {sent ? (
          <>
            <div className="h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold mb-2">Check your email</h1>
            <p className="text-sm text-stone-500 mb-6">
              We sent a password reset link to <strong>{email}</strong>
            </p>
            <Button variant="outline" onClick={() => setSent(false)}>Try another email</Button>
          </>
        ) : (
          <>
            <h1 className="text-2xl font-bold mb-2">Forgot your password?</h1>
            <p className="text-sm text-stone-500 mb-6">
              Enter your email and we&apos;ll send you a reset link.
            </p>
            <form onSubmit={handleSubmit} className="space-y-4 text-left">
              <Input label="Email address" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
              <Button type="submit" fullWidth loading={loading}>Send reset link</Button>
            </form>
          </>
        )}

        <p className="text-sm text-stone-500 mt-6">
          <Link href="/auth/login" className="text-primary-500 font-semibold hover:underline">
            ← Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}
