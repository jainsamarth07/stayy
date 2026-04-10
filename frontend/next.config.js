/**
 * Next.js configuration.
 * Enables standalone output for containerised deployment and configures remote image domains.
 * @type {import('next').NextConfig}
 */
const nextConfig = {
  output: "standalone",
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
