/**
 * @module Tabs
 * @description Horizontal tab navigation component with optional item counts.
 */
"use client";

import React from "react";

interface Tab {
  key: string;
  label: string;
  count?: number;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (key: string) => void;
}

/**
 * A horizontal tab bar. The active tab is highlighted with a bottom border.
 *
 * @param props - Tab configuration.
 * @param props.tabs - Array of tab definitions (key, label, optional count).
 * @param props.activeTab - The `key` of the currently selected tab.
 * @param props.onChange - Callback fired with the new tab key on selection.
 * @returns The rendered tab navigation element.
 */
export default function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onChange(tab.key)}
            className={`
              whitespace-nowrap border-b-2 py-3 px-1 text-sm font-medium transition-colors
              ${
                activeTab === tab.key
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
              }
            `}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={`ml-2 rounded-full px-2 py-0.5 text-xs ${
                  activeTab === tab.key
                    ? "bg-primary-100 text-primary-600"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </nav>
    </div>
  );
}
