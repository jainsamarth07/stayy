"use client";

import React, { useState } from "react";
import Button from "@/components/ui/button";
import Input from "@/components/ui/input";
import { Avatar } from "@/components/ui/index";
import { toast } from "@/components/ui/toast";
import { useAuthStore } from "@/stores/auth-store";
import { profileApi, getApiError } from "@/lib/api";
import { authClient } from "@/lib/auth-client";

export default function ProfilePage() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);
  const [pwForm, setPwForm] = useState({ current_password: "", new_password: "", confirm: "" });
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    phone: user?.phone || "",
  });

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handleSave = async () => {
    setLoading(true);
    try {
      const res = await profileApi.update(form);
      const updated = res.data;
      // Refresh auth store so the rest of the app sees new name/phone
      const current = useAuthStore.getState();
      if (current.user) {
        current.setSession(
          {
            ...current.user,
            full_name: updated.full_name ?? form.full_name,
            name: updated.full_name ?? form.full_name,
            phone: updated.phone ?? form.phone,
          },
          current.sessionToken
        );
      }
      setEditing(false);
      toast.success("Profile updated!");
    } catch (err: unknown) {
      toast.error(getApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (pwForm.new_password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    if (pwForm.new_password !== pwForm.confirm) {
      toast.error("Passwords do not match");
      return;
    }
    setPwLoading(true);
    const { error } = await authClient.changePassword({
      currentPassword: pwForm.current_password,
      newPassword: pwForm.new_password,
      revokeOtherSessions: true,
    });
    setPwLoading(false);
    if (error) {
      toast.error(error.message || "Failed to change password");
      return;
    }
    toast.success("Password changed!");
    setChangingPassword(false);
    setPwForm({ current_password: "", new_password: "", confirm: "" });
  };

  if (!user) return null;

  return (
    <main className="mx-auto max-w-3xl px-4 sm:px-6 py-8">
      <h1 className="text-2xl font-bold mb-8">Profile</h1>

      <div className="space-y-8">
        {/* Avatar */}
        <div className="flex items-center gap-6">
          <Avatar src={user.image} fallback={user.full_name || "U"} size="xl" />
          <div>
            <h2 className="text-lg font-semibold">{user.full_name}</h2>
            <p className="text-sm text-neutral-500">{user.email}</p>
            <p className="text-xs text-neutral-400 mt-1 capitalize">{user.role}</p>
          </div>
        </div>

        {/* Personal Info */}
        <div className="rounded-xl border p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">Personal Info</h3>
            {!editing && (
              <Button variant="outline" size="sm" onClick={() => setEditing(true)}>Edit</Button>
            )}
          </div>

          {editing ? (
            <div className="space-y-4">
              <Input label="Full name" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} />
              <Input label="Phone" type="tel" value={form.phone} onChange={(e) => update("phone", e.target.value)} />
              <div className="flex gap-3">
                <Button onClick={handleSave} loading={loading}>Save changes</Button>
                <Button variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {[
                { label: "Full name", value: user.full_name },
                { label: "Email", value: user.email },
                { label: "Phone", value: user.phone || "Not provided" },
                { label: "Role", value: user.role },
              ].map((item) => (
                <div key={item.label}>
                  <p className="text-xs text-neutral-500 uppercase tracking-wider">{item.label}</p>
                  <p className="text-sm mt-0.5">{item.value}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Security */}
        <div className="rounded-xl border p-6">
          <h3 className="text-lg font-semibold mb-4">Security</h3>
          {changingPassword ? (
            <div className="space-y-4">
              <Input label="Current password" type="password" value={pwForm.current_password} onChange={(e) => setPwForm((p) => ({ ...p, current_password: e.target.value }))} />
              <Input label="New password" type="password" value={pwForm.new_password} onChange={(e) => setPwForm((p) => ({ ...p, new_password: e.target.value }))} />
              <Input label="Confirm new password" type="password" value={pwForm.confirm} onChange={(e) => setPwForm((p) => ({ ...p, confirm: e.target.value }))} />
              <div className="flex gap-3">
                <Button loading={pwLoading} onClick={handleChangePassword}>Update Password</Button>
                <Button variant="outline" onClick={() => setChangingPassword(false)}>Cancel</Button>
              </div>
            </div>
          ) : (
            <Button variant="outline" onClick={() => setChangingPassword(true)}>Change Password</Button>
          )}
        </div>
      </div>
    </main>
  );
}
