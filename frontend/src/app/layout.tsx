import type { Metadata, Viewport } from "next";
import "./globals.css";
import { BottomNav } from "@/components/layout/BottomNav";
import Providers from "@/app/providers";
import { ServiceWorkerRegister } from "@/components/pwa/ServiceWorkerRegister";

export const metadata: Metadata = {
  title: "KisaanAI - AI-Powered Agriculture Analytics",
  description: "Get accurate commodity price predictions and expert advisory with KisaanAI.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "KisaanAI",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#22c55e",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="antialiased bg-background text-foreground">
        <Providers>
          <ServiceWorkerRegister />
          <main className="min-h-screen pb-20 md:pb-0">
            {children}
          </main>
          <BottomNav />
        </Providers>
      </body>
    </html>
  );
}
