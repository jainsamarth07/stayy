"use client";

import React, { useRef, useEffect, useState, useMemo } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { Sparkles, Send, X, Loader2, ExternalLink } from "lucide-react";
import { useAIChatStore } from "@/stores/aiChatStore";
import { useAuthStore } from "@/stores/auth-store";
import type { Property } from "@/types";

const SUGGESTED_PROMPTS = [
  "Find properties in Mumbai for 2 guests",
  "Plan a 3-day trip to Goa",
  "Show me budget stays under ₹2000/night",
];

interface PropertyResult {
  items?: Property[];
  total?: number;
  error?: string;
}

function PropertyCards({ data }: { data: PropertyResult }) {
  if (data.error) {
    return <p className="text-sm text-red-500">{data.error}</p>;
  }

  const items = data.items ?? [];
  if (items.length === 0) {
    return (
      <p className="text-sm text-neutral-500 italic">
        No properties found matching your criteria.
      </p>
    );
  }

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-semibold text-neutral-500">
        Found {data.total ?? items.length} properties
      </p>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {items.map((p) => {
          const img = p.images?.find((i) => i.is_primary) ?? p.images?.[0];
          return (
            <a
              key={p.id}
              href={`/properties/${p.id}`}
              className="flex-shrink-0 w-44 rounded-lg border border-neutral-200 bg-white overflow-hidden hover:shadow-md transition-shadow"
            >
              {img && (
                <img
                  src={img.image_url}
                  alt={p.title}
                  className="h-24 w-full object-cover"
                />
              )}
              <div className="p-2">
                <p className="text-xs font-semibold text-neutral-900 truncate">
                  {p.title}
                </p>
                <p className="text-xs text-neutral-500">{p.city}</p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs font-semibold text-rose-500">
                    ₹{p.price_per_night.toLocaleString("en-IN")}/night
                  </span>
                  <ExternalLink className="h-3 w-3 text-neutral-400" />
                </div>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}

function ToolPart({ part }: { part: { type: string; state: string; output?: unknown } }) {
  const toolName = part.type.replace("tool-", "");

  if (toolName === "search_properties") {
    if (part.state === "output-available") {
      return <PropertyCards data={part.output as PropertyResult} />;
    }
    return (
      <div className="flex items-center gap-2 text-sm text-neutral-500">
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Searching properties…
      </div>
    );
  }

  if (toolName === "generate_itinerary") {
    if (part.state !== "output-available") {
      return (
        <div className="flex items-center gap-2 text-sm text-neutral-500">
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
          Planning your itinerary…
        </div>
      );
    }
    return null;
  }

  return null;
}

export default function AiAgentChat() {
  const { isOpen, toggleChat, closeChat } = useAIChatStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const user = useAuthStore((s) => s.user);

  const chatId = useMemo(
    () => (user ? `ai-chat-${user.id}` : "ai-chat-guest"),
    [user]
  );

  const [input, setInput] = useState("");
  const { messages, sendMessage, status, setMessages } = useChat({
    id: chatId,
    transport: new DefaultChatTransport({ api: "/api/ai-agent" }),
  });
  const isLoading = status === "submitted" || status === "streaming";

  // Clear chat messages when user changes (login/logout)
  const prevUserIdRef = useRef<string | null>(user?.id ?? null);
  useEffect(() => {
    const currentUserId = user?.id ?? null;
    if (prevUserIdRef.current !== currentUserId) {
      setMessages([]);
      setInput("");
      prevUserIdRef.current = currentUserId;
    }
  }, [user, setMessages]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const submitPrompt = (text: string) => {
    sendMessage({ text });
  };

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={toggleChat}
        className="fixed bottom-5 right-5 z-50 flex items-center justify-center h-12 w-12 rounded-full bg-rose-500 text-white shadow-lg hover:bg-rose-600 active:scale-95 transition-all"
        aria-label="Toggle AI assistant"
      >
        {isOpen ? <X className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
      </button>

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-20 right-5 z-50 flex flex-col w-[400px] h-[500px] rounded-xl border border-neutral-200 bg-white shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-100 bg-neutral-50">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-rose-500" />
              <span className="text-sm font-semibold text-neutral-900">
                StayNest Assistant
              </span>
            </div>
            <button
              onClick={closeChat}
              className="text-neutral-400 hover:text-neutral-600 transition-colors"
              aria-label="Close chat"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
                <Sparkles className="h-8 w-8 text-rose-300" />
                <p className="text-sm text-neutral-500">
                  Hi! I can help you find properties and plan trips.
                </p>
                <div className="flex flex-col gap-2 w-full">
                  {SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => submitPrompt(prompt)}
                      className="text-left text-xs px-3 py-2 rounded-lg border border-neutral-200 hover:bg-neutral-50 text-neutral-700 transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id}>
                {msg.parts.map((part, idx) => {
                  if (part.type === "text" && part.text) {
                    return (
                      <div
                        key={idx}
                        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                          msg.role === "user"
                            ? "ml-auto bg-rose-500 text-white"
                            : "bg-neutral-100 text-neutral-800"
                        }`}
                      >
                        {part.text}
                      </div>
                    );
                  }

                  if (part.type.startsWith("tool-")) {
                    return (
                      <div key={idx} className="mt-2">
                        <ToolPart
                          part={part as { type: string; state: string; output?: unknown }}
                        />
                      </div>
                    );
                  }

                  return null;
                })}
              </div>
            ))}

            {/* Loading indicator */}
            {isLoading && messages[messages.length - 1]?.role === "user" && (
              <div className="flex items-center gap-1 text-neutral-400">
                <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 animate-bounce [animation-delay:-0.3s]" />
                <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 animate-bounce [animation-delay:-0.15s]" />
                <span className="h-1.5 w-1.5 rounded-full bg-neutral-400 animate-bounce" />
              </div>
            )}
          </div>

          {/* Input */}
          <form
            id="ai-chat-form"
            onSubmit={(e) => {
              e.preventDefault();
              if (!input.trim()) return;
              sendMessage({ text: input });
              setInput("");
            }}
            className="flex items-center gap-2 border-t border-neutral-100 px-3 py-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything…"
              className="flex-1 text-sm bg-transparent outline-none placeholder:text-neutral-400"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="flex items-center justify-center h-8 w-8 rounded-lg bg-rose-500 text-white disabled:opacity-40 hover:bg-rose-600 transition-colors"
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
