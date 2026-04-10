/**
 * @module AdminUsersPage
 * @description Admin user management page with search, role badges, and ban/unban actions.
 */
"use client";

import React, { useEffect, useState, useMemo } from "react";
import Button from "@/components/ui/button";
import { Avatar, Badge, Spinner } from "@/components/ui/index";
import { toast } from "@/components/ui/toast";
import type { User } from "@/types";
import { adminApi, getApiError } from "@/lib/api";

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await adminApi.listUsers(page);
        const data = res.data;
        setUsers(Array.isArray(data) ? data : data.items || []);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [page]);

  // Client-side search filter
  const filteredUsers = useMemo(() => {
    if (!search.trim()) return users;
    const q = search.toLowerCase();
    return users.filter(
      (u) =>
        u.full_name?.toLowerCase().includes(q) ||
        u.email?.toLowerCase().includes(q) ||
        u.role?.toLowerCase().includes(q)
    );
  }, [users, search]);

  const handleToggleStatus = async (userId: string) => {
    try {
      const res = await adminApi.toggleUserStatus(userId);
      const isActive = res.data.is_active;
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, is_active: isActive } : u))
      );
      toast.success(isActive ? "User activated" : "User deactivated");
    } catch (err: unknown) {
      toast.error(getApiError(err));
    }
  };

  const roleColor: Record<string, "default" | "success" | "info" | "error"> = {
    user: "default",
    host: "success",
    admin: "error",
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Users</h2>
        <input
          type="text"
          placeholder="Search users..."
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
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">User</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Email</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Role</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Status</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Joined</th>
                <th className="text-left text-xs font-medium text-gray-500 uppercase px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-10 text-sm text-gray-500">
                    No users found
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <Avatar src={u.avatar_url} fallback={u.full_name || "U"} size="sm" />
                        <span className="text-sm font-medium text-gray-900">
                          {u.full_name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <Badge variant={roleColor[u.role] || "default"}>{u.role}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={u.is_active ? "success" : "error"}>
                        {u.is_active ? "Active" : "Disabled"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggleStatus(u.id)}
                      >
                        {u.is_active ? "Disable" : "Enable"}
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
