"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

const ADMIN_ROLES = ["super_admin", "admin"];

export default function AdminRoot() {
  const router = useRouter();

  useEffect(() => {
    const stored = localStorage.getItem("loadmovegh_admin");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (ADMIN_ROLES.includes(parsed.role)) {
          router.replace("/dashboard");
          return;
        }
      } catch {
        /* invalid data — fall through to login */
      }
    }
    router.replace("/login");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="flex flex-col items-center gap-3">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-700 border-t-brand-500" />
        <p className="text-sm text-gray-400">Loading admin console...</p>
      </div>
    </div>
  );
}
