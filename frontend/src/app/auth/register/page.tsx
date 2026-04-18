"use client";

import React, { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { toast } from "@/components/ui/toast";
import { signUp, signIn } from "@/lib/auth-client";

export default function RegisterPageWrapper() {
  return (
    <Suspense fallback={null}>
      <RegisterPage />
    </Suspense>
  );
}

function RegisterPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlRole = searchParams.get("role");

  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<1 | 2>(1);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
    phone: "",
    role: (urlRole === "host" ? "host" : "user") as "user" | "host",
    agree_terms: false,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const update = (field: string, value: string | boolean) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const validateStep1 = () => {
    const errs: Record<string, string> = {};
    if (!form.first_name.trim()) errs.first_name = "First name is required";
    if (!form.last_name.trim()) errs.last_name = "Last name is required";
    if (!form.email) errs.email = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = "Invalid email";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const validateStep2 = () => {
    const errs: Record<string, string> = {};
    if (!form.password) errs.password = "Password is required";
    else if (form.password.length < 8) errs.password = "At least 8 characters";
    if (form.password !== form.confirm_password)
      errs.confirm_password = "Passwords don't match";
    if (!form.agree_terms) errs.agree_terms = "You must accept terms";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateStep2()) return;

    setLoading(true);
    const { error } = await signUp.email({
      name: `${form.first_name} ${form.last_name}`.trim(),
      email: form.email,
      password: form.password,
      // Custom fields passed through BetterAuth
      role: form.role,
      phone: form.phone || undefined,
    } as Parameters<typeof signUp.email>[0]);

    if (error) {
      setLoading(false);
      toast.error(error.message || "Registration failed");
      return;
    }

    toast.success("Account created! Welcome to StayNest.");
    setLoading(false);

    if (form.role === "host") {
      router.push("/dashboard/membership");
    } else {
      router.push("/");
    }
  };

  const handleGoogle = () => {
    signIn.social({ provider: "google", callbackURL: "/" });
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <svg viewBox="0 0 32 32" className="h-10 w-10 text-primary-500 fill-current">
              <path d="M16 3C16 3 6 11 6 18c0 5.523 4.477 10 10 10s10-4.477 10-10C26 11 16 3 16 3z" opacity="0.2"/>
              <path d="M16 2c-.4 0-.8.15-1.1.43C13.5 3.8 5 11.5 5 18c0 6.075 4.925 11 11 11s11-4.925 11-11c0-6.5-8.5-14.2-9.9-15.57A1.5 1.5 0 0016 2zm0 3.4C18.2 7.5 25 13.6 25 18c0 4.97-4.03 9-9 9s-9-4.03-9-9c0-4.4 6.8-10.5 9-12.6z"/>
              <ellipse cx="16" cy="20" rx="4" ry="3" opacity="0.35"/>
            </svg>
          </div>
          <h1 className="text-2xl font-bold">Create your account</h1>
          <p className="text-sm text-stone-500 mt-1">Join StayNest — no commissions, ever.</p>
        </div>

        {/* Social signup - only on step 1 */}
        {step === 1 && (
          <>
            <button
              onClick={handleGoogle}
              className="w-full flex items-center justify-center gap-3 border rounded-lg py-2.5 px-4 text-sm font-semibold hover:bg-stone-50 transition mb-4"
            >
              <svg viewBox="0 0 24 24" className="h-5 w-5">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </button>
            <div className="relative mb-4">
              <div className="absolute inset-0 flex items-center"><div className="w-full border-t" /></div>
              <div className="relative flex justify-center text-sm">
                <span className="bg-white px-3 text-stone-500">or</span>
              </div>
            </div>
          </>
        )}

        {/* Progress bar */}
        <div className="flex gap-2 mb-6">
          {[1, 2].map((s) => (
            <div key={s} className={`h-1 flex-1 rounded-full ${s <= step ? "bg-primary-500" : "bg-stone-200"}`} />
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {step === 1 ? (
            <>
              <div className="grid grid-cols-2 gap-3">
                <Input label="First name" value={form.first_name} onChange={(e) => update("first_name", e.target.value)} error={errors.first_name} autoComplete="given-name" />
                <Input label="Last name" value={form.last_name} onChange={(e) => update("last_name", e.target.value)} error={errors.last_name} autoComplete="family-name" />
              </div>
              <Input label="Email" type="email" placeholder="you@example.com" value={form.email} onChange={(e) => update("email", e.target.value)} error={errors.email} autoComplete="email" />
              <Input label="Phone (optional)" type="tel" placeholder="+1 (555) 000-0000" value={form.phone} onChange={(e) => update("phone", e.target.value)} autoComplete="tel" />

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-2">I want to…</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: "user" as const, label: "Book stays", desc: "Find amazing places" },
                    { value: "host" as const, label: "List property", desc: "Earn with zero commissions" },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => update("role", opt.value)}
                      className={`p-3 rounded-xl border-2 text-left transition ${form.role === opt.value ? "border-primary-500 bg-primary-50" : "border-stone-200 hover:border-stone-300"}`}
                    >
                      <p className="text-sm font-semibold">{opt.label}</p>
                      <p className="text-xs text-stone-500">{opt.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              <Button type="button" fullWidth onClick={() => validateStep1() && setStep(2)}>
                Continue
              </Button>
            </>
          ) : (
            <>
              <Input label="Password" type="password" placeholder="Min. 8 characters" value={form.password} onChange={(e) => update("password", e.target.value)} error={errors.password} autoComplete="new-password" />
              <Input label="Confirm password" type="password" placeholder="Re-enter your password" value={form.confirm_password} onChange={(e) => update("confirm_password", e.target.value)} error={errors.confirm_password} autoComplete="new-password" />

              <div className="space-y-1.5">
                {[
                  { test: form.password.length >= 8, label: "At least 8 characters" },
                  { test: /[A-Z]/.test(form.password), label: "One uppercase letter" },
                  { test: /[a-z]/.test(form.password), label: "One lowercase letter" },
                  { test: /\d/.test(form.password), label: "One number" },
                ].map((rule) => (
                  <div key={rule.label} className="flex items-center gap-2 text-xs">
                    <span className={rule.test ? "text-green-500" : "text-stone-300"}>{rule.test ? "✓" : "○"}</span>
                    <span className={rule.test ? "text-green-700" : "text-stone-500"}>{rule.label}</span>
                  </div>
                ))}
              </div>

              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.agree_terms}
                  onChange={(e) => update("agree_terms", e.target.checked)}
                  className="mt-1 rounded border-stone-300 text-primary-500 focus:ring-primary-500"
                />
                <span className="text-sm text-stone-600">
                  I agree to the{" "}
                  <Link href="/terms" className="text-primary-500 hover:underline">Terms</Link>
                  {" "}and{" "}
                  <Link href="/privacy" className="text-primary-500 hover:underline">Privacy Policy</Link>
                </span>
              </label>
              {errors.agree_terms && <p className="text-sm text-red-600">{errors.agree_terms}</p>}

              <div className="flex gap-3">
                <Button type="button" variant="outline" onClick={() => setStep(1)} className="flex-1">Back</Button>
                <Button type="submit" loading={loading} className="flex-1">Create account</Button>
              </div>
            </>
          )}
        </form>

        <p className="text-center text-sm text-stone-500 mt-6">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-primary-500 font-semibold hover:underline">Log in</Link>
        </p>
      </div>
    </div>
  );
}
