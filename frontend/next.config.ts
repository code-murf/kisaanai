import type { NextConfig } from "next";
import path from "path";

const rawApiProxyTarget =
  process.env.API_PROXY_TARGET ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

const apiProxyTarget = rawApiProxyTarget
  .replace(/\/+$/, "")
  .replace(/\/api(?:\/v1)?$/i, "");

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
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiProxyTarget}/api/v1/:path*`,
      },
      {
        source: "/static/:path*",
        destination: `${apiProxyTarget}/static/:path*`,
      },
    ];
  },
};

export default nextConfig;
