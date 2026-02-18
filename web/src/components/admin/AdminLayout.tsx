"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAdmin } from "@/context/AdminContext";
import Sidebar from "@/components/admin/Sidebar";
import TopNavbar from "@/components/admin/TopNavbar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, hasAdminAccess, user, logout } = useAdmin();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace("/admin/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return null;

  /* Authenticated but role is NOT admin/super_admin → Access Denied */
  if (!hasAdminAccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-red-600/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/3 right-1/4 w-64 h-64 bg-orange-600/8 rounded-full blur-3xl" />
        </div>
        <div className="relative w-full max-w-md text-center">
          <div className="h-16 w-16 rounded-full bg-red-600/20 border-2 border-red-500/30 flex items-center justify-center mx-auto mb-5">
            <svg className="h-8 w-8 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Access Denied</h1>
          <p className="text-gray-400 mb-2">
            Your account (<span className="text-white font-medium">{user?.email}</span>) has the role{" "}
            <span className="inline-flex items-center rounded-md bg-gray-800 px-2 py-0.5 text-xs font-bold text-amber-400 ring-1 ring-amber-500/30">
              {user?.role}
            </span>
          </p>
          <p className="text-gray-500 text-sm mb-8">
            Only users with <span className="text-white font-semibold">admin</span> or{" "}
            <span className="text-white font-semibold">super_admin</span> roles can access the admin console.
            Contact your system administrator if you believe this is an error.
          </p>
          <div className="flex items-center justify-center gap-3">
            <a
              href="https://www.loadmovegh.com"
              className="inline-flex items-center gap-2 rounded-lg bg-gray-800 border border-gray-700 px-5 py-2.5 text-sm font-semibold text-gray-300 hover:bg-gray-700 hover:text-white transition"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
              </svg>
              Go to Main Site
            </a>
            <button
              onClick={logout}
              className="inline-flex items-center gap-2 rounded-lg bg-red-600/20 border border-red-800/30 px-5 py-2.5 text-sm font-semibold text-red-400 hover:bg-red-600/30 hover:text-red-300 transition"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" />
              </svg>
              Sign Out & Re-login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopNavbar />
        <main className="flex-1 p-4 sm:p-6 max-w-[1600px]">
          {children}
        </main>
      </div>
    </div>
  );
}
