"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { signOut } from "@/lib/auth-client";
import { Avatar } from "@/components/ui/index";
import { Menu } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [profileOpen, setProfileOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const isHost = user?.role === "host" || user?.role === "admin";

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-40 bg-[#FFFAF5] border-b border-stone-200 shadow-sm">
      <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <svg viewBox="0 0 32 32" className="h-8 w-8 text-primary-500 fill-current" aria-hidden="true">
              <path d="M16 3C16 3 6 11 6 18c0 5.523 4.477 10 10 10s10-4.477 10-10C26 11 16 3 16 3z" opacity="0.2"/>
              <path d="M16 2c-.4 0-.8.15-1.1.43C13.5 3.8 5 11.5 5 18c0 6.075 4.925 11 11 11s11-4.925 11-11c0-6.5-8.5-14.2-9.9-15.57A1.5 1.5 0 0016 2zm0 3.4C18.2 7.5 25 13.6 25 18c0 4.97-4.03 9-9 9s-9-4.03-9-9c0-4.4 6.8-10.5 9-12.6z"/>
              <ellipse cx="16" cy="20" rx="4" ry="3" opacity="0.35"/>
            </svg>
            <span className="text-xl font-bold text-primary-600 hidden md:block tracking-tight">
              StayNest
            </span>
          </Link>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {isAuthenticated && isHost && (
              <Link
                href="/dashboard"
                className="hidden lg:block text-sm font-semibold px-4 py-2.5 rounded-lg hover:bg-primary-50 text-primary-600 transition"
              >
                Host Dashboard
              </Link>
            )}

            {!isAuthenticated && (
              <Link
                href="/auth/register?role=host"
                className="hidden lg:block text-sm font-semibold px-4 py-2.5 rounded-lg hover:bg-primary-50 text-primary-600 transition"
              >
                Start Hosting
              </Link>
            )}

            {/* User menu */}
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 border border-stone-300 rounded-lg py-1.5 px-2.5 hover:shadow-md transition bg-white"
              >
                <Menu className="h-4 w-4 text-stone-500" />
                <Avatar
                  src={user?.image}
                  fallback={user ? user.full_name || "U" : "U"}
                  size="sm"
                />
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-xl bg-white shadow-xl border border-stone-200 py-2 z-50">
                  {isAuthenticated ? (
                    <>
                      <div className="px-4 py-2 border-b border-stone-100">
                        <p className="text-sm font-semibold truncate">
                          {user?.full_name}
                        </p>
                        <p className="text-xs text-stone-500 truncate">{user?.email}</p>
                      </div>
                      <Link
                        href="/messages"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-stone-50 font-semibold"
                      >
                        Messages
                      </Link>
                      <Link
                        href="/bookings"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-stone-50 font-semibold"
                      >
                        Trips
                      </Link>
                      <Link
                        href="/profile"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-stone-50"
                      >
                        Profile
                      </Link>
                      {isHost && (
                        <>
                          <hr className="my-1" />
                          <Link
                            href="/dashboard"
                            onClick={() => setProfileOpen(false)}
                            className="block px-4 py-2.5 text-sm hover:bg-stone-50"
                          >
                            Host Dashboard
                          </Link>
                          <Link
                            href="/dashboard/properties"
                            onClick={() => setProfileOpen(false)}
                            className="block px-4 py-2.5 text-sm hover:bg-stone-50"
                          >
                            My Listings
                          </Link>
                        </>
                      )}
                      {user?.role === "admin" && (
                        <>
                          <hr className="my-1" />
                          <Link
                            href="/admin"
                            onClick={() => setProfileOpen(false)}
                            className="block px-4 py-2.5 text-sm hover:bg-stone-50"
                          >
                            Admin Panel
                          </Link>
                        </>
                      )}
                      <hr className="my-1" />
                      <button
                        onClick={async () => {
                          setProfileOpen(false);
                          await signOut();
                          router.push("/");
                        }}
                        className="block w-full text-left px-4 py-2.5 text-sm hover:bg-stone-50"
                      >
                        Log out
                      </button>
                    </>
                  ) : (
                    <>
                      <Link
                        href="/auth/login"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-stone-50 font-semibold"
                      >
                        Log in
                      </Link>
                      <Link
                        href="/auth/register"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-stone-50"
                      >
                        Sign up
                      </Link>
                      <hr className="my-1" />
                      <Link
                        href="/auth/register?role=host"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-stone-50"
                      >
                        Start Hosting
                      </Link>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
