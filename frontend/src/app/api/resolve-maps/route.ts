/**
 * Server-side URL resolver for shortened Google Maps links.
 * Follows redirects (e.g. maps.app.goo.gl → full Google Maps URL)
 * so the client can extract coordinates without CORS issues.
 */
import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const url = request.nextUrl.searchParams.get("url");
  if (!url) {
    return NextResponse.json({ error: "Missing url parameter" }, { status: 400 });
  }

  // Only allow known Google Maps domains
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return NextResponse.json({ error: "Invalid URL" }, { status: 400 });
  }

  const allowed = [
    "maps.app.goo.gl",
    "goo.gl",
    "maps.google.com",
    "www.google.com",
  ];
  if (!allowed.includes(parsed.hostname)) {
    return NextResponse.json({ error: "URL domain not allowed" }, { status: 400 });
  }

  try {
    // HEAD with redirect:follow gives us the final URL without downloading the body
    const response = await fetch(url, {
      method: "GET",
      redirect: "follow",
      headers: {
        // Mimic a browser so Google serves the full redirect chain
        "User-Agent":
          "Mozilla/5.0 (compatible; StayNest/1.0; +https://staynest.app)",
      },
    });
    return NextResponse.json({ resolvedUrl: response.url });
  } catch {
    return NextResponse.json({ error: "Failed to resolve URL" }, { status: 500 });
  }
}
