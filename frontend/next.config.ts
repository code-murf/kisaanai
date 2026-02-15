import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname, ".."),
  /* experimental: {
    webpackBuildWorker: false,
    workerThreads: true,
    cpus: 1,
  }, */
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
