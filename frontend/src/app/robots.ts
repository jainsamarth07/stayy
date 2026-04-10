/**
 * Robots.txt generation for search engine crawlers.
 * @see https://nextjs.org/docs/app/api-reference/file-conventions/metadata/robots
 */
import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/api/", "/admin/", "/dashboard/"],
      },
    ],
    sitemap: `${process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"}/sitemap.xml`,
  };
}
