import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LoadMoveGH Admin — Management Console",
  description:
    "Enterprise admin dashboard for managing the LoadMoveGH freight exchange platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans">{children}</body>
    </html>
  );
}
