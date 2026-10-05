import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow cross-origin requests for HMR
  experimental: {
    allowedDevOrigins: ['192.168.56.1'],
  },
};

export default nextConfig;
