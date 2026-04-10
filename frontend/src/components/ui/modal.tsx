/**
 * @module Modal
 * @description Accessible modal dialog component with backdrop, configurable size, and close handling.
 */
"use client";

import React from "react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
}

const sizeClasses = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-xl",
};

/**
 * A modal dialog rendered as a fixed overlay with a translucent backdrop.
 *
 * @param props - Modal configuration.
 * @param props.isOpen - Controls visibility of the modal.
 * @param props.onClose - Callback invoked when the backdrop or close button is clicked.
 * @param props.title - Optional title displayed in the modal header.
 * @param props.size - Width preset (`sm` | `md` | `lg` | `xl`). Defaults to `"md"`.
 * @returns The rendered modal or `null` when closed.
 */
export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
}: ModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        data-testid="modal-backdrop"
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className={`
            relative w-full ${sizeClasses[size]} transform rounded-xl bg-white
            shadow-2xl transition-all p-6
          `}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          {title && (
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              <button
                onClick={onClose}
                aria-label="Close"
                className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}

          {/* Body */}
          {children}
        </div>
      </div>
    </div>
  );
}
