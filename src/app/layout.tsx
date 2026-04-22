import type { Metadata, Viewport } from "next";
import { ZCOOL_KuaiLe } from "next/font/google";
import "./globals.css";

const zcoolKuaile = ZCOOL_KuaiLe({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-zcool",
  display: "swap",
});

export const metadata: Metadata = {
  title: "课文背诵 — 法语闪卡",
  description: "中法双语闪卡，走遍法国课文背诵",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#f8f9fc",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" className={zcoolKuaile.variable}>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
