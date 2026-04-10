"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";
import { signOut } from "@/lib/auth-client";
import { Avatar } from "@/components/ui/index";
import { Search, Menu, Globe } from "lucide-react";

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
    <header className="sticky top-0 z-40 bg-white border-b shadow-sm">
      <div className="mx-auto max-w-container px-4 sm:px-8 md:px-10 xl:px-20">
        <div className="flex items-center justify-between h-16 md:h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-1.5">
            <svg viewBox="0 0 32 32" className="h-8 w-8 text-rose-500 fill-current" aria-hidden="true">
              <path d="M16 1c2.008 0 3.463.963 4.751 3.269l.533 1.025c1.954 3.83 6.114 12.54 7.1 14.836l.145.353c.667 1.591.91 2.472.96 3.396l.01.415.001.228c0 4.062-2.877 6.478-6.357 6.478-2.224 0-4.556-1.258-6.709-3.386l-.257-.26-.172-.179h-.001l-.176.185c-2.044 2.1-4.267 3.42-6.414 3.615l-.28.019-.267.006C5.377 31 2.5 28.584 2.5 24.522l.005-.469c.026-.928.23-1.768.83-3.244l.216-.524c.966-2.298 5.127-11.011 7.074-14.83l.54-1.036C12.537 1.963 13.992 1 16 1z" />
            </svg>
            <span className="text-xl font-bold text-rose-500 hidden md:block">
              staynest
            </span>
          </Link>

          {/* Center: Search bar */}
          <div
            className="hidden md:flex items-center border rounded-full shadow-sm hover:shadow-md transition cursor-pointer"
            onClick={() => router.push("/properties")}
          >
            <button className="px-4 py-2 text-sm font-semibold border-r">
              Anywhere
            </button>
            <button className="px-4 py-2 text-sm font-semibold border-r hidden lg:block">
              Any week
            </button>
            <button className="px-4 py-2 text-sm text-neutral-500 flex items-center gap-2">
              Add guests
              <span className="bg-rose-500 text-white rounded-full p-1.5">
                <Search className="h-3 w-3" />
              </span>
            </button>
          </div>

          {/* Mobile search button */}
          <button
            className="md:hidden flex items-center gap-3 border rounded-full w-full max-w-[280px] mx-4 p-2 shadow-sm"
            onClick={() => router.push("/properties")}
          >
            <Search className="h-4 w-4 ml-2 text-neutral-800" />
            <div className="flex-1 text-left">
              <p className="text-xs font-semibold leading-none">Anywhere</p>
              <p className="text-[11px] text-neutral-500 leading-none mt-0.5">Any week · Add guests</p>
            </div>
          </button>

          {/* Right side */}
          <div className="flex items-center gap-2">
            {isAuthenticated && isHost && (
              <Link
                href="/dashboard"
                className="hidden lg:block text-sm font-semibold px-4 py-3 rounded-full hover:bg-neutral-100 transition"
              >
                Switch to hosting
              </Link>
            )}

            {!isAuthenticated && (
              <Link
                href="/auth/register?role=host"
                className="hidden lg:block text-sm font-semibold px-4 py-3 rounded-full hover:bg-neutral-100 transition"
              >
                Become a Host
              </Link>
            )}

            <button className="hidden md:block p-3 rounded-full hover:bg-neutral-100 transition">
              <Globe className="h-4 w-4" />
            </button>

            {/* User menu */}
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 border rounded-full py-1 px-2 hover:shadow-md transition"
              >
                <Menu className="h-4 w-4 text-neutral-600" />
                <Avatar
                  src={user?.image}
                  fallback={user ? user.full_name || "U" : "U"}
                  size="sm"
                />
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-xl bg-white shadow-xl border py-2 z-50">
                  {isAuthenticated ? (
                    <>
                      <div className="px-4 py-2 border-b">
                        <p className="text-sm font-semibold truncate">
                          {user?.full_name}
                        </p>
                        <p className="text-xs text-neutral-500 truncate">{user?.email}</p>
                      </div>
                      <Link
                        href="/messages"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-neutral-50 font-semibold"
                      >
                        Messages
                      </Link>
                      <Link
                        href="/bookings"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-neutral-50 font-semibold"
                      >
                        Trips
                      </Link>
                      <Link
                        href="/profile"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-neutral-50"
                      >
                        Profile
                      </Link>
                      {isHost && (
                        <>
                          <hr className="my-1" />
                          <Link
                            href="/dashboard"
                            onClick={() => setProfileOpen(false)}
                            className="block px-4 py-2.5 text-sm hover:bg-neutral-50"
                          >
                            Host Dashboard
                          </Link>
                          <Link
                            href="/dashboard/properties"
                            onClick={() => setProfileOpen(false)}
                            className="block px-4 py-2.5 text-sm hover:bg-neutral-50"
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
                            className="block px-4 py-2.5 text-sm hover:bg-neutral-50"
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
                        className="block w-full text-left px-4 py-2.5 text-sm hover:bg-neutral-50"
                      >
                        Log out
                      </button>
                    </>
                  ) : (
                    <>
                      <Link
                        href="/auth/login"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-neutral-50 font-semibold"
                      >
                        Log in
                      </Link>
                      <Link
                        href="/auth/register"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-neutral-50"
                      >
                        Sign up
                      </Link>
                      <hr className="my-1" />
                      <Link
                        href="/auth/register?role=host"
                        onClick={() => setProfileOpen(false)}
                        className="block px-4 py-2.5 text-sm hover:bg-neutral-50"
                      >
                        Become a Host
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
