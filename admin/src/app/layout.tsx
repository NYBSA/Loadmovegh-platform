import type { Metadata } from "next";
import "./globals.css";
import { AdminProvider } from "@/context/AdminContext";

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
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen font-sans">
        <AdminProvider>{children}</AdminProvider>
      </body>
    </html>
  );
}
