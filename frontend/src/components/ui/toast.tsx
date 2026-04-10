/**
 * @module Toast
 * @description Global toast notification system with smooth enter/exit animations,
 * auto-dismiss progress bar, and proper SVG icons. Provides a `toast` API object for
 * programmatically showing success/error/info/warning messages and a `ToastContainer`
 * component that renders active toasts.
 */
"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";

type ToastType = "success" | "error" | "info" | "warning";

interface ToastData {
  id: string;
  type: ToastType;
  message: string;
  exiting?: boolean;
}

const TOAST_DURATION = 4000;
const EXIT_DURATION = 300;

/* ---------- Styling ---------- */

const containerStyles: Record<ToastType, string> = {
  success: "bg-white border-l-4 border-l-emerald-500 shadow-lg shadow-emerald-500/10",
  error: "bg-white border-l-4 border-l-rose-500 shadow-lg shadow-rose-500/10",
  info: "bg-white border-l-4 border-l-sky-500 shadow-lg shadow-sky-500/10",
  warning: "bg-white border-l-4 border-l-amber-500 shadow-lg shadow-amber-500/10",
};

const iconBgStyles: Record<ToastType, string> = {
  success: "bg-emerald-50 text-emerald-600",
  error: "bg-rose-50 text-rose-600",
  info: "bg-sky-50 text-sky-600",
  warning: "bg-amber-50 text-amber-600",
};

const progressStyles: Record<ToastType, string> = {
  success: "bg-emerald-500",
  error: "bg-rose-500",
  info: "bg-sky-500",
  warning: "bg-amber-500",
};

/* ---------- SVG Icons ---------- */

function SuccessIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
    </svg>
  );
}

function InfoIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
    </svg>
  );
}

function WarningIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M4 4l8 8M12 4l-8 8" />
    </svg>
  );
}

const typeIcons: Record<ToastType, React.FC> = {
  success: SuccessIcon,
  error: ErrorIcon,
  info: InfoIcon,
  warning: WarningIcon,
};

const typeLabels: Record<ToastType, string> = {
  success: "Success",
  error: "Error",
  info: "Info",
  warning: "Warning",
};

/* ---------- Global toast state ---------- */
let toastListeners: Array<(toasts: ToastData[]) => void> = [];
let toasts: ToastData[] = [];

function notify() {
  toastListeners.forEach((l) => l([...toasts]));
}

/**
 * Global toast API. Call `toast.success(msg)`, `toast.error(msg)`, etc.
 */
export const toast = {
  success(message: string) { add("success", message); },
  error(message: string) { add("error", message); },
  info(message: string) { add("info", message); },
  warning(message: string) { add("warning", message); },
};

function add(type: ToastType, message: string) {
  const id = Math.random().toString(36).slice(2);
  toasts = [...toasts, { id, type, message }];
  notify();
  // Auto-dismiss: start exit animation then remove
  setTimeout(() => startExit(id), TOAST_DURATION);
}

function startExit(id: string) {
  toasts = toasts.map((t) => (t.id === id ? { ...t, exiting: true } : t));
  notify();
  setTimeout(() => remove(id), EXIT_DURATION);
}

function remove(id: string) {
  toasts = toasts.filter((t) => t.id !== id);
  notify();
}

/* ---------- Single Toast ---------- */

function ToastItem({ data }: { data: ToastData }) {
  const [hovered, setHovered] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const startTimeRef = useRef(Date.now());
  const remainingRef = useRef(TOAST_DURATION);

  // Pause auto-dismiss on hover
  useEffect(() => {
    if (hovered) {
      if (timerRef.current) clearTimeout(timerRef.current);
      remainingRef.current -= Date.now() - startTimeRef.current;
    } else {
      startTimeRef.current = Date.now();
      timerRef.current = setTimeout(
        () => startExit(data.id),
        Math.max(remainingRef.current, 500)
      );
    }
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [hovered, data.id]);

  const handleDismiss = useCallback(() => {
    startExit(data.id);
  }, [data.id]);

  const Icon = typeIcons[data.type];

  return (
    <div
      role="alert"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={[
        "relative flex items-start gap-3 rounded-xl border border-neutral-200/60 px-4 py-3.5 w-[380px] max-w-[calc(100vw-2rem)] overflow-hidden backdrop-blur-sm",
        containerStyles[data.type],
        data.exiting
          ? "animate-toast-exit"
          : "animate-toast-enter",
      ].join(" ")}
    >
      {/* Icon */}
      <div className={`flex-shrink-0 rounded-full p-1.5 ${iconBgStyles[data.type]}`}>
        <Icon />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pt-0.5">
        <p className="text-xs font-semibold uppercase tracking-wide text-neutral-400 mb-0.5">
          {typeLabels[data.type]}
        </p>
        <p className="text-sm text-neutral-700 leading-snug">{data.message}</p>
      </div>

      {/* Dismiss */}
      <button
        onClick={handleDismiss}
        aria-label="Dismiss notification"
        className="flex-shrink-0 mt-0.5 p-1 rounded-lg text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 transition-colors"
      >
        <CloseIcon />
      </button>

      {/* Auto-dismiss progress bar */}
      {!data.exiting && (
        <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-neutral-100 overflow-hidden rounded-b-xl">
          <div
            className={`h-full rounded-full ${progressStyles[data.type]}`}
            style={{
              animation: `toast-progress ${TOAST_DURATION}ms linear forwards`,
              animationPlayState: hovered ? "paused" : "running",
            }}
          />
        </div>
      )}
    </div>
  );
}

/* ---------- Toast Container ---------- */

/**
 * Renders active toast notifications in a fixed top-center container.
 * Mount this component once in the application shell.
 */
export function ToastContainer() {
  const [items, setItems] = useState<ToastData[]>([]);

  useEffect(() => {
    toastListeners.push(setItems);
    return () => {
      toastListeners = toastListeners.filter((l) => l !== setItems);
    };
  }, []);

  if (items.length === 0) return null;

  return (
    <div className="fixed top-5 right-5 z-[100] flex flex-col gap-3 pointer-events-none">
      {items.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <ToastItem data={t} />
        </div>
      ))}
    </div>
  );
}
