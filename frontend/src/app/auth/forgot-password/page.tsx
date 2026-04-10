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
          <svg viewBox="0 0 32 32" className="h-10 w-10 text-rose-500 fill-current">
            <path d="M16 1c2.008 0 3.463.963 4.751 3.269l.533 1.025c1.954 3.83 6.114 12.54 7.1 14.836l.145.353c.667 1.591.91 2.472.96 3.396l.01.415.001.228c0 4.062-2.877 6.478-6.357 6.478-2.224 0-4.556-1.258-6.709-3.386l-.257-.26-.172-.179h-.001l-.176.185c-2.044 2.1-4.267 3.42-6.414 3.615l-.28.019-.267.006C5.377 31 2.5 28.584 2.5 24.522l.005-.469c.026-.928.23-1.768.83-3.244l.216-.524c.966-2.298 5.127-11.011 7.074-14.83l.54-1.036C12.537 1.963 13.992 1 16 1z" />
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
            <p className="text-sm text-neutral-500 mb-6">
              We sent a password reset link to <strong>{email}</strong>
            </p>
            <Button variant="outline" onClick={() => setSent(false)}>Try another email</Button>
          </>
        ) : (
          <>
            <h1 className="text-2xl font-bold mb-2">Forgot your password?</h1>
            <p className="text-sm text-neutral-500 mb-6">
              Enter your email and we&apos;ll send you a reset link.
            </p>
            <form onSubmit={handleSubmit} className="space-y-4 text-left">
              <Input label="Email address" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
              <Button type="submit" fullWidth loading={loading}>Send reset link</Button>
            </form>
          </>
        )}

        <p className="text-sm text-neutral-500 mt-6">
          <Link href="/auth/login" className="text-rose-500 font-semibold hover:underline">
            ← Back to login
          </Link>
        </p>
      </div>
    </div>
  );
}
