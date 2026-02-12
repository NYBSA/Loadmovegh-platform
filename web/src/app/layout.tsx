import type { Metadata } from "next";
import "./globals.css";
import Providers from "./providers";

export const metadata: Metadata = {
  title: "LoadMoveGH — Ghana Freight Marketplace",
  description:
    "Connect shippers with reliable couriers across Ghana. AI-powered pricing, real-time tracking, and secure escrow payments.",
  metadataBase: new URL("https://www.loadmovegh.com"),
  openGraph: {
    siteName: "LoadMoveGH",
    url: "https://www.loadmovegh.com",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
