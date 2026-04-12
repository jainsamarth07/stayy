/**
 * @module ConversationPage
 * @description Real-time chat view for direct messaging between guests and hosts.
 */
"use client";

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Avatar, Spinner } from "@/components/ui/index";
import Button from "@/components/ui/button";
import { toast } from "@/components/ui/toast";
import { messageApi, getApiError } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import type { Message } from "@/types";

export default function ConversationPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [convMeta, setConvMeta] = useState<{
    other_party_name?: string;
    property_title?: string;
    property_id?: string;
    guest_id?: string;
    host_id?: string;
    current_user_id?: string;
  }>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const refreshMessages = useCallback(async () => {
    try {
      const msgs = await messageApi.getMessages(id);
      const data = msgs.data;
      setMessages(Array.isArray(data) ? data : data.items || []);
      // Silently mark any newly-received messages as read
      messageApi.markConversationRead(id).catch(() => {/* best-effort */});
    } catch {
      // silent
    }
  }, [id]);

  useEffect(() => {
    const load = async () => {
      try {
        const [msgRes, convRes] = await Promise.all([
          messageApi.getMessages(id),
          messageApi.getConversation(id),
        ]);
        const data = msgRes.data;
        setMessages(Array.isArray(data) ? data : data.items || []);
        setConvMeta(convRes.data);
        // Mark all incoming messages as read now that the user is viewing them
        messageApi.markConversationRead(id).catch(() => {/* best-effort */});
      } catch {
        toast.error("Conversation not found");
        router.push("/messages");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id, router]);

  useEffect(() => { scrollToBottom(); }, [messages]);

  // Poll for new messages
  useEffect(() => {
    const interval = setInterval(refreshMessages, 10000);
    return () => clearInterval(interval);
  }, [refreshMessages]);

  const handleSend = async () => {
    if (!newMessage.trim() || sending) return;
    setSending(true);
    try {
      const res = await messageApi.sendMessage(id, newMessage);
      setMessages((prev) => [...prev, res.data]);
      setNewMessage("");
    } catch (err: unknown) {
      toast.error(getApiError(err));
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (loading) {
    return <div className="flex justify-center py-20"><Spinner size="lg" /></div>;
  }

  return (
    <main className="flex flex-col h-[calc(100vh-64px)]">
      {/* Conversation header */}
      <div className="border-b border-gray-200 bg-white px-4 py-3">
        <div className="flex items-center gap-3 max-w-3xl mx-auto">
          <button
            onClick={() => router.push("/messages")}
            className="text-gray-500 hover:text-gray-700 lg:hidden"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <Avatar fallback={convMeta.other_party_name?.charAt(0) || "U"} size="md" />
          <div className="min-w-0 flex-1">
            <h2 className="text-sm font-semibold text-gray-900 truncate">
              {convMeta.other_party_name || "Conversation"}
            </h2>
            {convMeta.property_title && (
              <p className="text-xs text-gray-500 truncate">{convMeta.property_title}</p>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.length === 0 && (
            <p className="text-center text-sm text-gray-400 py-8">Start the conversation!</p>
          )}
          {messages.map((msg) => {
            const isMe = convMeta.current_user_id
              ? msg.sender_id === convMeta.current_user_id
              : msg.sender_id === user?.backendId;
            return (
              <div key={msg.id} className={`flex ${isMe ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[70%] rounded-2xl px-4 py-2.5 ${isMe ? "bg-rose-600 text-white rounded-br-md" : "bg-gray-100 text-gray-900 rounded-bl-md"}`}>
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  <p className={`text-[10px] mt-1 ${isMe ? "text-rose-200" : "text-gray-400"}`}>
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="max-w-3xl mx-auto flex items-end gap-2">
          <textarea
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-rose-200 focus:border-rose-500"
            style={{ maxHeight: "120px" }}
          />
          <Button onClick={handleSend} loading={sending} disabled={!newMessage.trim()} className="rounded-xl">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </Button>
        </div>
      </div>
    </main>
  );
}
