import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname, ".."),
  // Type checking is enforced in CI via `tsc --noEmit`.
  // This avoids intermittent Windows spawn EPERM during `next build`.
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "yjdmobzdaeznstzeinod.supabase.co",
      },
    ],
  },
};

export default nextConfig;
