import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The Docker image consumes Next's standalone server output. Vercel builds
  // its own Next runtime, so keep standalone output off only on Vercel.
  ...(process.env.VERCEL ? {} : { output: "standalone" as const }),
  turbopack: {
    // Neon CLI's root package-lock.json must not change the frontend's root.
    root: process.cwd(),
  },
  reactStrictMode: true,
};

export default nextConfig;
