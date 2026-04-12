/**
 * @module MessagesPage
 * @description Conversations inbox listing all message threads for the authenticated user.
 */
"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Avatar, Spinner } from "@/components/ui/index";
import EmptyState from "@/components/ui/empty-state";
import { messageApi } from "@/lib/api";
import type { Conversation } from "@/types";

export default function MessagesPage() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const res = await messageApi.listConversations();
      const data = res.data;
      setConversations(Array.isArray(data) ? data : data.items || []);
    } catch {
      setConversations([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // Re-fetch when the tab regains focus so unread counts reflect recent reads
    const onFocus = () => load();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
      <main className="mx-auto max-w-3xl px-4 sm:px-6 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Messages</h1>

        {loading ? (
          <div className="flex justify-center py-20"><Spinner size="lg" /></div>
        ) : conversations.length === 0 ? (
          <EmptyState
            title="No messages yet"
            description="When you contact a host or receive a message, it will appear here."
            icon={
              <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            }
          />
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <Link
                key={conv.id}
                href={`/messages/${conv.id}`}
                className="flex items-center gap-4 rounded-xl p-4 hover:bg-gray-50 transition"
              >
                <Avatar
                  fallback={conv.other_party_name?.charAt(0) || "U"}
                  size="lg"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-900 truncate">
                      {conv.other_party_name || "User"}
                    </h3>
                    <span className="text-xs text-gray-400 shrink-0">
                      {conv.updated_at
                        ? new Date(conv.updated_at).toLocaleDateString()
                        : ""}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 truncate">
                    {conv.property_title || "Property"}
                  </p>
                  <p className="text-sm text-gray-600 truncate mt-0.5">
                    {conv.last_message?.content || "No messages yet"}
                  </p>
                </div>
                {conv.unread_count > 0 && (
                  <span className="bg-rose-600 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center shrink-0">
                    {conv.unread_count}
                  </span>
                )}
              </Link>
            ))}
          </div>
        )}
      </main>
  );
}
