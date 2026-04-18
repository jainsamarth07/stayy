/**
 * @module Sidebar
 * @description Vertical sidebar navigation used in dashboard and admin layouts.
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface SidebarItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

interface SidebarProps {
  items: SidebarItem[];
  title?: string;
}

/**
 * A vertical sidebar navigation panel with active-state highlighting.
 *
 * @param props.items - Navigation items, each with `href`, `label`, and `icon`.
 * @param props.title - Optional heading rendered above the links.
 * @returns The sidebar `<aside>` element (visible only on `lg+` screens).
 */
export default function Sidebar({ items, title }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 hidden lg:block">
      {title && (
        <h2 className="text-lg font-semibold text-gray-900 mb-4 px-3">
          {title}
        </h2>
      )}
      <nav className="space-y-1">
        {items.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-primary-50 text-primary-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <span className={active ? "text-primary-600" : "text-gray-400"}>
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
