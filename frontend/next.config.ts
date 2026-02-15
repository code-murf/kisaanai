import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'standalone', // For Docker deployment
  experimental: {
    // reactCompiler: true,
  },
  // Allow images from external sources
  images: {
    domains: ['yjdmobzdaeznstzeinod.supabase.co'],
  },
};

export default nextConfig;
