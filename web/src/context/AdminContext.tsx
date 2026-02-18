"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

/* ── Types ───────────────────────────────────────── */

export type AdminRole = "super_admin" | "admin" | "moderator" | "viewer";

export interface AdminUser {
  email: string;
  name: string;
  role: AdminRole;
  avatar?: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  type: "info" | "warning" | "error" | "success";
  time: string;
  read: boolean;
}

const ADMIN_ROLES: AdminRole[] = ["super_admin", "admin"];

interface AdminContextValue {
  user: AdminUser | null;
  isAuthenticated: boolean;
  hasAdminAccess: boolean;
  login: (email: string, name: string, role: AdminRole) => void;
  logout: () => void;
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  setSidebarOpen: (v: boolean) => void;
  toggleSidebarCollapsed: () => void;
  darkMode: boolean;
  toggleDarkMode: () => void;
  notifications: Notification[];
  unreadCount: number;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearNotification: (id: string) => void;
  activeSection: string;
  setActiveSection: (s: string) => void;
}

const AdminContext = createContext<AdminContextValue | null>(null);

/* ── Demo Notifications ──────────────────────────── */

const DEMO_NOTIFICATIONS: Notification[] = [
  { id: "n1", title: "Critical Fraud Alert", message: "QuickMove GH flagged for rapid deposit-withdraw cycles. Score: 89/100.", type: "error", time: "25m ago", read: false },
  { id: "n2", title: "New User Pending Approval", message: "Kofi Transport Ltd submitted KYC documents for review.", type: "info", time: "2h ago", read: false },
  { id: "n3", title: "Compliance Deadline", message: "QuickHaul insurance certificate missing — due Feb 13.", type: "warning", time: "3h ago", read: false },
  { id: "n4", title: "Revenue Milestone", message: "Platform crossed GHS 2.8M monthly revenue.", type: "success", time: "5h ago", read: false },
  { id: "n5", title: "Dispute Escalated", message: "Dispute #D-221 escalated — shipper requests refund of GHS 4,100.", type: "warning", time: "6h ago", read: true },
  { id: "n6", title: "New Fake Company Alert", message: "PhantomShip Ltd — 12 listings, 0 trips, KYC rejected.", type: "error", time: "8h ago", read: true },
  { id: "n7", title: "System Update", message: "AI Fraud Detection model v2.3 deployed successfully.", type: "success", time: "1d ago", read: true },
];

/* ── Provider ────────────────────────────────────── */

export function AdminProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AdminUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>(DEMO_NOTIFICATIONS);
  const [activeSection, setActiveSection] = useState("overview");

  useEffect(() => {
    const stored = localStorage.getItem("loadmovegh_admin");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        const role: AdminRole = parsed.role || "viewer";
        if (ADMIN_ROLES.includes(role)) {
          setUser({
            email: parsed.email || "admin@loadmovegh.com",
            name: parsed.name || "System Admin",
            role,
          });
        } else {
          localStorage.removeItem("loadmovegh_admin");
          setUser(null);
        }
      } catch {
        localStorage.removeItem("loadmovegh_admin");
        setUser(null);
      }
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("loadmovegh_admin_dark");
    if (stored === "true") {
      setDarkMode(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("loadmovegh_admin_sidebar");
    if (stored === "collapsed") setSidebarCollapsed(true);
  }, []);

  const login = useCallback((email: string, name: string, role: AdminRole) => {
    const userData = { email, name, role, token: "admin_demo_token", loggedInAt: new Date().toISOString() };
    localStorage.setItem("loadmovegh_admin", JSON.stringify(userData));
    setUser({ email, name, role });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("loadmovegh_admin");
    setUser(null);
    router.push("/admin/login");
  }, [router]);

  const toggleDarkMode = useCallback(() => {
    setDarkMode((prev) => {
      const next = !prev;
      localStorage.setItem("loadmovegh_admin_dark", String(next));
      if (next) {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
      return next;
    });
  }, []);

  const toggleSidebarCollapsed = useCallback(() => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("loadmovegh_admin_sidebar", next ? "collapsed" : "expanded");
      return next;
    });
  }, []);

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const clearNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;
  const hasAdminAccess = !!user && ADMIN_ROLES.includes(user.role);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-700 border-t-purple-500" />
      </div>
    );
  }

  return (
    <AdminContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        hasAdminAccess,
        login,
        logout,
        sidebarOpen,
        sidebarCollapsed,
        setSidebarOpen,
        toggleSidebarCollapsed,
        darkMode,
        toggleDarkMode,
        notifications,
        unreadCount,
        markAsRead,
        markAllAsRead,
        clearNotification,
        activeSection,
        setActiveSection,
      }}
    >
      {children}
    </AdminContext.Provider>
  );
}

export function useAdmin() {
  const ctx = useContext(AdminContext);
  if (!ctx) throw new Error("useAdmin must be used inside <AdminProvider>");
  return ctx;
}
