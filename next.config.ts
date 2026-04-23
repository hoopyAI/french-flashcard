import type { NextConfig } from "next";

const isStaticExport = process.env.STATIC_EXPORT === "1";

const nextConfig: NextConfig = {
  // Include `.dev.tsx` / `.dev.ts` page/route files only outside static export.
  // That keeps /editor and /api/editor alive for `next dev` but invisible to
  // the static build used by Cloudflare Pages.
  pageExtensions: isStaticExport
    ? ["tsx", "ts", "jsx", "js"]
    : ["dev.tsx", "dev.ts", "tsx", "ts", "jsx", "js"],
  ...(isStaticExport ? { output: "export", trailingSlash: true } : {}),
};

export default nextConfig;

import('@opennextjs/cloudflare').then(m => m.initOpenNextCloudflareForDev());
