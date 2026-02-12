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

/* ── Types ────────────────────────────────────────── */
export type UserRole = "courier" | "shipper" | "admin";

export interface User {
  id: string;
  fullName: string;
  email: string;
  phone: string;
  role: UserRole;
  company?: string;
  vehicleType?: string;
  avatar?: string;
  verified: boolean;
  createdAt: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string, role: UserRole) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

export interface SignupData {
  fullName: string;
  email: string;
  phone: string;
  password: string;
  role: UserRole;
  company?: string;
  vehicleType?: string;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/* ── Helpers ──────────────────────────────────────── */
const STORAGE_KEY = "loadmovegh_auth";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function generateId(): string {
  return "usr_" + Math.random().toString(36).slice(2, 11);
}

function persistAuth(user: User, token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ user, token }));
  }
}

function loadAuth(): { user: User; token: string } | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function clearAuth() {
  if (typeof window !== "undefined") {
    localStorage.removeItem(STORAGE_KEY);
  }
}

/* ── Provider ─────────────────────────────────────── */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true,
  });

  /* Hydrate from localStorage on mount */
  useEffect(() => {
    const saved = loadAuth();
    if (saved) {
      setState({ user: saved.user, token: saved.token, isLoading: false });
    } else {
      setState((s) => ({ ...s, isLoading: false }));
    }
  }, []);

  /* ── Login ───────────────────────────────────────── */
  const login = useCallback(
    async (email: string, password: string, role: UserRole) => {
      setState((s) => ({ ...s, isLoading: true }));

      try {
        /* Try real API first */
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });

        if (res.ok) {
          const data = await res.json();
          const user: User = data.user;
          const token: string = data.access_token;
          persistAuth(user, token);
          setState({ user, token, isLoading: false });
          return;
        }
      } catch {
        /* API unreachable — fall through to demo mode */
      }

      /* ── Demo / Offline Mode ──────────────────────── */
      await new Promise((r) => setTimeout(r, 800));

      if (!email || !password) {
        setState((s) => ({ ...s, isLoading: false }));
        throw new Error("Email and password are required");
      }

      const demoUser: User = {
        id: generateId(),
        fullName: role === "courier" ? "Kwame Asante" : "Ama Enterprises",
        email,
        phone: "+233 24 000 0000",
        role,
        company: role === "shipper" ? "Ama Enterprises Ltd" : undefined,
        vehicleType: role === "courier" ? "Box Truck" : undefined,
        verified: true,
        createdAt: new Date().toISOString(),
      };
      const demoToken = "demo_" + Math.random().toString(36).slice(2);
      persistAuth(demoUser, demoToken);
      setState({ user: demoUser, token: demoToken, isLoading: false });
    },
    [],
  );

  /* ── Signup ──────────────────────────────────────── */
  const signup = useCallback(async (data: SignupData) => {
    setState((s) => ({ ...s, isLoading: true }));

    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (res.ok) {
        const result = await res.json();
        const user: User = result.user;
        const token: string = result.access_token;
        persistAuth(user, token);
        setState({ user, token, isLoading: false });
        return;
      }
    } catch {
      /* API unreachable — demo mode */
    }

    /* Demo mode */
    await new Promise((r) => setTimeout(r, 1000));

    if (!data.email || !data.password || !data.fullName) {
      setState((s) => ({ ...s, isLoading: false }));
      throw new Error("All required fields must be filled");
    }

    const newUser: User = {
      id: generateId(),
      fullName: data.fullName,
      email: data.email,
      phone: data.phone,
      role: data.role,
      company: data.company,
      vehicleType: data.vehicleType,
      verified: false,
      createdAt: new Date().toISOString(),
    };
    const token = "demo_" + Math.random().toString(36).slice(2);
    persistAuth(newUser, token);
    setState({ user: newUser, token, isLoading: false });
  }, []);

  /* ── Logout ──────────────────────────────────────── */
  const logout = useCallback(() => {
    clearAuth();
    setState({ user: null, token: null, isLoading: false });
  }, []);

  const value: AuthContextValue = {
    ...state,
    login,
    signup,
    logout,
    isAuthenticated: !!state.user && !!state.token,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/* ── Hook ─────────────────────────────────────────── */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

/* ── Auth Guard Component ─────────────────────────── */
export function RequireAuth({
  role,
  children,
}: {
  role: UserRole;
  children: ReactNode;
}) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/${role}/login`);
    }
    if (!isLoading && isAuthenticated && user?.role !== role) {
      router.replace(`/${user?.role}/dashboard`);
    }
  }, [isLoading, isAuthenticated, user, role, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
          <p className="text-sm text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || user?.role !== role) {
    return null;
  }

  return <>{children}</>;
}
