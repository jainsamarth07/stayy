/**
 * Next.js configuration.
 * Enables standalone output for containerised deployment and configures remote image domains.
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  output: "standalone",

  // mapbox-gl uses browser-specific APIs; tell Next.js not to try SSR-transpiling it.
  // The map components themselves are wrapped in next/dynamic with ssr:false.
  transpilePackages: ["mapbox-gl"],

  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "9000",
        pathname: "/staynest-images/**",
      },
    ],
  },
};

module.exports = nextConfig;
