import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow opening UI via http://127.0.0.1:3000 (not only localhost)
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
