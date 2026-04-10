import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { getSessionCookie } from "better-auth/cookies";

const publicPaths = ["/", "/auth/login", "/auth/register", "/auth/forgot-password", "/properties"];
const hostPaths = ["/dashboard"];
const adminPaths = ["/admin"];

function isPublic(pathname: string) {
  return publicPaths.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
}

function matchesAny(pathname: string, paths: string[]) {
  return paths.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Always allow auth API routes, static assets, and public pages
  if (
    pathname.startsWith("/api/auth") ||
    pathname.startsWith("/_next") ||
    pathname.includes(".") ||
    isPublic(pathname)
  ) {
    return NextResponse.next();
  }

  // Check for BetterAuth session cookie (fast, no DB lookup)
  const sessionCookie = getSessionCookie(request);

  if (!sessionCookie) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // For role-based routes we rely on the client-side ProtectedRoute component
  // since the session cookie doesn't carry role claims (that requires a DB lookup).
  // The middleware only gates: authenticated vs unauthenticated.
  // Fine-grained role enforcement happens in ProtectedRoute or server components.
  if (matchesAny(pathname, [...hostPaths, ...adminPaths])) {
    // Allow through — ProtectedRoute handles role check client-side
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
