"use client";

import Link from "next/link";
import Image from "next/image";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth, type UserRole } from "@/context/AuthContext";

/* ── Vehicle fleet data ──────────────────────────── */
const vehicles = [
  { name: "Container Truck", image: "/vehicles/container-truck.png" },
  { name: "Big Van",         image: "/vehicles/big-van.png" },
  { name: "Heavy Truck",     image: "/vehicles/heavy-truck.png" },
  { name: "Flatbed",         image: "/vehicles/flatbed.png" },
  { name: "Refrigerated",    image: "/vehicles/refrigerated.png" },
  { name: "Motorcycle Truck", image: "/vehicles/motorcycle.png" },
  { name: "Tipper",          image: "/vehicles/tipper.png" },
  { name: "Small Van",       image: "/vehicles/small-van.png" },
];

const VEHICLE_TYPES = [
  "Motorcycle Truck", "Small Van", "Big Van", "Flatbed",
  "Box Truck", "Container Truck", "Refrigerated", "Tipper", "Heavy Truck",
];

const BUSINESS_TYPES = [
  "Manufacturing", "Agriculture & Farming", "Construction",
  "Retail & E-commerce", "Food & Beverages", "Mining",
  "Logistics Provider", "Import / Export", "Healthcare", "Other",
];

const GHANA_REGIONS = [
  "Greater Accra", "Ashanti", "Western", "Central", "Eastern",
  "Northern", "Volta", "Bono", "Upper East", "Upper West",
  "Savannah", "North East", "Oti", "Ahafo", "Bono East", "Western North",
];

/* ── Earnings estimate data ──────────────────────── */
const EARNINGS_PER_KM: Record<string, number> = {
  "Motorcycle Truck": 2.5, "Small Van": 3.8, "Big Van": 5.2, "Flatbed": 6.5,
  "Box Truck": 7.0, "Container Truck": 9.5, "Refrigerated": 10.0, "Tipper": 8.0, "Heavy Truck": 11.0,
};

export default function HomePage() {
  const { signup, login, logout, isLoading, isAuthenticated, user } = useAuth();
  const router = useRouter();
  const authRef = useRef<HTMLDivElement>(null);

  /* ── Tabs ──────────────────────────────────────── */
  const [activeRole, setActiveRole] = useState<UserRole>("shipper");
  const [authMode, setAuthMode] = useState<"signup" | "login">("signup");

  /* ── Signup form state ─────────────────────────── */
  const [form, setForm] = useState({
    fullName: "", email: "", phone: "", password: "",
    company: "", businessType: "", vehicleType: "",
  });

  /* ── Login form state ──────────────────────────── */
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  /* ── Calculator state ──────────────────────────── */
  const [calcStep, setCalcStep] = useState(1);
  const [calcVehicles, setCalcVehicles] = useState<{ type: string; mileage: number }[]>([]);
  const [calcVehicleType, setCalcVehicleType] = useState("");
  const [calcMileage, setCalcMileage] = useState(1500);
  const [calcRegion, setCalcRegion] = useState("");
  const [calcResult, setCalcResult] = useState<number | null>(null);

  function addCalcVehicle() {
    if (!calcVehicleType) return;
    setCalcVehicles((prev) => [...prev, { type: calcVehicleType, mileage: calcMileage }]);
    setCalcVehicleType("");
    setCalcMileage(1500);
  }

  function undoCalcVehicle() {
    setCalcVehicles((prev) => prev.slice(0, -1));
  }

  function calculateEarnings() {
    if (calcVehicles.length === 0 && calcVehicleType) {
      addCalcVehicle();
    }
    const allVehicles = calcVehicleType && calcVehicles.length === 0
      ? [{ type: calcVehicleType, mileage: calcMileage }]
      : calcVehicles;

    const weekly = allVehicles.reduce((sum, v) => {
      const rate = EARNINGS_PER_KM[v.type] || 5;
      return sum + v.mileage * rate;
    }, 0);
    setCalcResult(Math.round(weekly * 4.33));
    setCalcStep(3);
  }

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
    setError("");
  }

  function resetAll() {
    setForm({ fullName: "", email: "", phone: "", password: "", company: "", businessType: "", vehicleType: "" });
    setLoginEmail(""); setLoginPassword("");
    setError(""); setSuccess(false);
  }

  function switchRole(role: UserRole) {
    setActiveRole(role);
    resetAll();
  }

  function switchAuthMode(mode: "signup" | "login") {
    setAuthMode(mode);
    setError("");
  }

  function scrollToAuth(role?: UserRole, mode?: "signup" | "login") {
    if (role) switchRole(role);
    if (mode) setAuthMode(mode);
    setTimeout(() => {
      authRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 50);
  }

  /* ── Signup handler ────────────────────────────── */
  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!form.fullName || !form.email || !form.phone || !form.password) {
      setError("Please fill in all required fields"); return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters"); return;
    }
    if (activeRole === "courier" && !form.vehicleType) {
      setError("Please select your vehicle type"); return;
    }
    if (activeRole === "shipper" && !form.company) {
      setError("Please enter your company name"); return;
    }
    try {
      await signup({
        fullName: form.fullName, email: form.email, phone: form.phone,
        password: form.password, role: activeRole,
        company: activeRole === "shipper" ? form.company : undefined,
        vehicleType: activeRole === "courier" ? form.vehicleType : undefined,
      });
      setSuccess(true);
      setTimeout(() => router.push(`/${activeRole}/dashboard`), 600);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Signup failed. Please try again.");
    }
  }

  /* ── Login handler ─────────────────────────────── */
  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!loginEmail || !loginPassword) {
      setError("Please enter your email and password"); return;
    }
    try {
      await login(loginEmail, loginPassword, activeRole);
      setSuccess(true);
      setTimeout(() => router.push(`/${activeRole}/dashboard`), 600);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid credentials. Try again.");
    }
  }

  return (
    <div className="min-h-screen bg-cream-100">
      {/* ── Navbar ─────────────────────────────────────── */}
      <nav className="border-b border-accent-200/50 bg-cream-100/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="LoadMoveGH" width={48} height={48} className="h-10 w-auto object-contain" />
              <span className="text-xl font-bold text-gray-900">
                LoadMove<span className="text-brand-700">GH</span>
              </span>
            </div>
            <div className="flex items-center gap-3">
              {isAuthenticated && user ? (
                <>
                  <Link href={`/${user.role}/dashboard`}
                    className="hidden sm:flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-brand-700 transition">
                    <span className="h-7 w-7 rounded-full bg-brand-100 flex items-center justify-center text-xs font-bold text-brand-800">
                      {user.fullName.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)}
                    </span>
                    <span className="max-w-[120px] truncate">{user.fullName}</span>
                  </Link>
                  <Link href={`/${user.role}/dashboard`} className="btn-secondary text-sm">Dashboard</Link>
                  <button onClick={() => { logout(); router.push("/"); }} className="btn-primary text-sm !bg-red-500 hover:!bg-red-600 !text-white">Logout</button>
                </>
              ) : (
                <>
                  <button onClick={() => scrollToAuth("courier", "login")} className="btn-secondary text-sm">Courier Login</button>
                  <button onClick={() => scrollToAuth("shipper", "login")} className="btn-primary text-sm">Shipper Login</button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* ── Hero + Earnings Calculator ──────────────────── */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <section className="pt-16 pb-12 lg:pt-24 lg:pb-16">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            {/* Left — Hero Text */}
            <div>
              <span className="badge-yellow mb-6 inline-block">
                Trusted by 500+ businesses across Ghana
              </span>
              <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl lg:text-[3.5rem] leading-[1.1]">
                Be your own boss. Set your own hours.{" "}
                <span className="text-brand-700">Make your own money.</span>
              </h1>
              <p className="mt-6 text-lg leading-8 text-gray-600 max-w-xl">
                LoadMoveGH is Ghana&apos;s biggest freight marketplace. It gets you access to thousands of daily loads. And everything owner drivers need to make more money and grow.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row items-start gap-4">
                <button onClick={() => scrollToAuth("courier", "signup")} className="btn-primary px-8 py-3.5 text-base">
                  Apply now
                </button>
                <button onClick={() => scrollToAuth("shipper", "signup")} className="btn-secondary px-8 py-3.5 text-base">
                  Post a Load
                </button>
              </div>
            </div>

            {/* Right — Earnings Calculator */}
            <div className="rounded-2xl bg-brand-50 border border-brand-200/60 p-6 sm:p-8 shadow-lg">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Calculate your<br />potential earnings
              </h2>

              {/* Step indicators */}
              <div className="flex items-center gap-3 mb-6">
                <button onClick={() => { setCalcStep(1); setCalcResult(null); }}
                  className={`flex items-center gap-2 ${calcStep >= 1 ? "text-brand-700" : "text-gray-400"}`}>
                  <span className={`h-3 w-3 rounded-full ${calcStep >= 1 ? "bg-brand-600" : "bg-gray-300"}`} />
                  <span className="text-sm font-medium">Your vehicles</span>
                </button>
                <div className={`flex-1 h-px ${calcStep >= 2 ? "bg-brand-400" : "bg-gray-300"}`} />
                <button onClick={() => { if (calcVehicles.length > 0 || calcVehicleType) { setCalcStep(2); setCalcResult(null); } }}
                  className={`flex items-center gap-2 ${calcStep >= 2 ? "text-brand-700" : "text-gray-400"}`}>
                  <span className={`h-3 w-3 rounded-full ${calcStep >= 2 ? "bg-brand-600" : "bg-gray-300"}`} />
                  <span className="text-sm font-medium">Select a region</span>
                </button>
              </div>

              {calcStep === 1 && (
                <div className="space-y-5">
                  <p className="text-sm text-gray-600">What vehicles do you have?</p>

                  {/* Added vehicles */}
                  {calcVehicles.length > 0 && (
                    <div className="space-y-2">
                      {calcVehicles.map((v, i) => (
                        <div key={i} className="flex items-center justify-between rounded-lg bg-white border border-brand-200 px-4 py-2.5 text-sm">
                          <span className="font-medium text-gray-800">{v.type}</span>
                          <span className="text-gray-500">{v.mileage.toLocaleString()} km/week</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 block">Vehicle type</label>
                    <select
                      className="input rounded-full"
                      value={calcVehicleType}
                      onChange={(e) => setCalcVehicleType(e.target.value)}
                    >
                      <option value="">Select a vehicle type</option>
                      {VEHICLE_TYPES.map((vt) => (<option key={vt} value={vt}>{vt}</option>))}
                    </select>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-sm font-medium text-gray-700">Mileage per week</label>
                      <span className="text-sm font-bold text-gray-900">{calcMileage.toLocaleString()}</span>
                    </div>
                    <input
                      type="range" min={100} max={5000} step={100}
                      value={calcMileage}
                      onChange={(e) => setCalcMileage(Number(e.target.value))}
                      className="w-full h-2 bg-brand-200 rounded-full appearance-none cursor-pointer accent-brand-600"
                    />
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>100 km</span><span>5,000 km</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <button onClick={addCalcVehicle} disabled={!calcVehicleType}
                      className="btn-secondary text-sm disabled:opacity-40">
                      Add
                    </button>
                    <button onClick={undoCalcVehicle} disabled={calcVehicles.length === 0}
                      className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 disabled:opacity-40 transition">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3" />
                      </svg>
                      Undo
                    </button>
                  </div>

                  <button
                    onClick={() => { if (calcVehicleType || calcVehicles.length > 0) setCalcStep(2); }}
                    disabled={!calcVehicleType && calcVehicles.length === 0}
                    className="w-full btn-purple py-3 text-base disabled:opacity-40"
                  >
                    Continue
                  </button>
                  <p className="text-center text-xs text-gray-400">Takes 30 seconds</p>
                </div>
              )}

              {calcStep === 2 && (
                <div className="space-y-5">
                  <p className="text-sm text-gray-600">Where do you operate?</p>

                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-1.5 block">Select a region</label>
                    <select
                      className="input rounded-full"
                      value={calcRegion}
                      onChange={(e) => setCalcRegion(e.target.value)}
                    >
                      <option value="">Choose your region</option>
                      {GHANA_REGIONS.map((r) => (<option key={r} value={r}>{r}</option>))}
                    </select>
                  </div>

                  <div className="flex gap-3">
                    <button onClick={() => setCalcStep(1)} className="btn-secondary flex-1 py-3 text-base">Back</button>
                    <button onClick={calculateEarnings} disabled={!calcRegion}
                      className="flex-1 btn-purple py-3 text-base disabled:opacity-40">
                      Calculate
                    </button>
                  </div>
                </div>
              )}

              {calcStep === 3 && calcResult !== null && (
                <div className="text-center py-4 space-y-4">
                  <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-accent-100 mb-2">
                    <svg className="h-8 w-8 text-accent-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Estimated monthly earnings</p>
                    <p className="text-4xl font-extrabold text-brand-700 mt-1">
                      GHS {calcResult.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      Based on {calcVehicles.length || 1} vehicle{(calcVehicles.length || 1) > 1 ? "s" : ""} in {calcRegion}
                    </p>
                  </div>
                  <div className="flex flex-col gap-3 pt-2">
                    <button onClick={() => scrollToAuth("courier", "signup")} className="btn-primary w-full py-3 text-base">
                      Start Earning — Sign Up Free
                    </button>
                    <button onClick={() => { setCalcStep(1); setCalcResult(null); setCalcVehicles([]); setCalcRegion(""); }}
                      className="text-sm text-brand-600 hover:text-brand-800 font-medium transition">
                      Recalculate
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ── Vehicle Fleet Carousel ──────────────────── */}
        <section className="py-12 -mx-4 sm:-mx-6 lg:-mx-8">
          <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl mb-2">
            Our Fleet
          </h2>
          <p className="text-center text-sm text-gray-500 mb-8">
            From motorcycles to heavy haulers — we move it all across Ghana
          </p>
          <div className="relative bg-gradient-to-b from-cream-50 to-cream-200/50 py-8 overflow-hidden">
            <div className="carousel-wrapper overflow-hidden">
              <div className="vehicle-track">
                {[...vehicles, ...vehicles].map((v, i) => (
                  <div key={`${v.name}-${i}`} className="vehicle-card flex-shrink-0 flex flex-col items-center mx-4 sm:mx-6 lg:mx-8 cursor-pointer group" style={{ width: "160px" }}>
                    <div className="relative w-[140px] h-[90px] sm:w-[160px] sm:h-[100px] flex items-center justify-center">
                      <Image src={v.image} alt={v.name} width={160} height={100} className="object-contain max-h-full" priority={i < 8} />
                    </div>
                    <span className="vehicle-name mt-3 text-xs sm:text-sm font-semibold text-gray-700 text-center whitespace-nowrap bg-white/80 backdrop-blur-sm px-3 py-1 rounded-full shadow-sm border border-gray-200/60">
                      {v.name}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div className="road-line mt-6 mx-8 rounded-full" />
          </div>
        </section>

        {/* ── Stats ─────────────────────────────────────── */}
        <section className="py-12">
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
            {[
              { label: "Loads Posted", value: "12,480+" },
              { label: "Verified Couriers", value: "3,200+" },
              { label: "Routes Covered", value: "16 Regions" },
              { label: "On-Time Rate", value: "94.7%" },
            ].map((stat) => (
              <div key={stat.label} className="card text-center">
                <p className="text-2xl font-bold text-brand-700 sm:text-3xl">{stat.value}</p>
                <p className="mt-1 text-sm text-gray-500">{stat.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Sign Up & Login ────────────────────────────── */}
        <section id="auth" ref={authRef} className="py-16 scroll-mt-24">
          <div className="mx-auto max-w-xl">
            <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl mb-2">
              {authMode === "signup" ? "Get Started — It's Free" : "Welcome Back"}
            </h2>
            <p className="text-center text-sm text-gray-500 mb-8">
              {authMode === "signup"
                ? "Create your account in under a minute and start moving freight today"
                : "Log in to your account and continue where you left off"}
            </p>

            {/* Role Toggle */}
            <div className="flex rounded-xl bg-white/60 border border-brand-200/40 p-1 mb-4">
              <button onClick={() => switchRole("shipper")}
                className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition-all ${activeRole === "shipper" ? "bg-white text-brand-700 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z" />
                </svg>
                I&apos;m a Shipper
              </button>
              <button onClick={() => switchRole("courier")}
                className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold transition-all ${activeRole === "courier" ? "bg-white text-brand-700 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 0 1-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 0 0-3.213-9.193 2.056 2.056 0 0 0-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 0 0-10.026 0 1.106 1.106 0 0 0-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
                </svg>
                I&apos;m a Courier
              </button>
            </div>

            {/* Sign Up / Log In Toggle */}
            <div className="flex rounded-lg border border-brand-200/40 bg-white/60 p-0.5 mb-6">
              <button onClick={() => switchAuthMode("signup")}
                className={`flex-1 rounded-md py-2 text-sm font-semibold transition-all ${authMode === "signup" ? "bg-brand-600 text-white shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
                Sign Up
              </button>
              <button onClick={() => switchAuthMode("login")}
                className={`flex-1 rounded-md py-2 text-sm font-semibold transition-all ${authMode === "login" ? "bg-brand-600 text-white shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
                Log In
              </button>
            </div>

            {/* Card */}
            <div className="card p-6 sm:p-8">
              {success ? (
                <div className="text-center py-8">
                  <div className="mx-auto h-14 w-14 rounded-full bg-emerald-100 flex items-center justify-center mb-4">
                    <svg className="h-7 w-7 text-emerald-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">{authMode === "signup" ? "Account Created!" : "Welcome Back!"}</h3>
                  <p className="mt-1 text-sm text-gray-500">Redirecting to your dashboard...</p>
                  <div className="mt-4 h-1 w-32 mx-auto rounded-full bg-gray-100 overflow-hidden">
                    <div className="h-full bg-brand-600 rounded-full animate-pulse" style={{ width: "100%" }} />
                  </div>
                </div>
              ) : authMode === "signup" ? (
                <>
                  <div className="mb-6">
                    <h3 className="text-lg font-bold text-gray-900">
                      {activeRole === "shipper" ? "Shipper Sign Up" : "Courier Sign Up"}
                    </h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {activeRole === "shipper"
                        ? "Post loads and manage shipments across Ghana"
                        : "Find loads, bid competitively, and earn with every delivery"}
                    </p>
                  </div>
                  {error && (
                    <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-start gap-2">
                      <svg className="h-5 w-5 flex-shrink-0 mt-0.5 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                      </svg>
                      {error}
                    </div>
                  )}
                  <form onSubmit={handleSignup} className="space-y-4">
                    <div>
                      <label className="label">Full Name</label>
                      <input type="text" className="input" placeholder={activeRole === "shipper" ? "Ama Mensah" : "Kwame Asante"} value={form.fullName} onChange={(e) => update("fullName", e.target.value)} />
                    </div>
                    {activeRole === "shipper" && (
                      <div>
                        <label className="label">Company / Business Name</label>
                        <input type="text" className="input" placeholder="Ama Enterprises Ltd" value={form.company} onChange={(e) => update("company", e.target.value)} />
                      </div>
                    )}
                    {activeRole === "shipper" && (
                      <div>
                        <label className="label">Business Type</label>
                        <select className="input" value={form.businessType} onChange={(e) => update("businessType", e.target.value)}>
                          <option value="">Select business type</option>
                          {BUSINESS_TYPES.map((bt) => (<option key={bt} value={bt}>{bt}</option>))}
                        </select>
                      </div>
                    )}
                    {activeRole === "courier" && (
                      <div>
                        <label className="label">Vehicle Type</label>
                        <div className="grid grid-cols-3 gap-2">
                          {VEHICLE_TYPES.map((vt) => (
                            <button key={vt} type="button" onClick={() => update("vehicleType", vt)}
                              className={`rounded-lg border px-2.5 py-2 text-xs font-medium transition ${form.vehicleType === vt ? "border-brand-600 bg-brand-50 text-brand-700 ring-1 ring-brand-600" : "border-gray-200 bg-white text-gray-600 hover:border-gray-300"}`}
                            >{vt}</button>
                          ))}
                        </div>
                      </div>
                    )}
                    <div>
                      <label className="label">Email Address</label>
                      <input type="email" className="input" placeholder={activeRole === "shipper" ? "ama@enterprise.com" : "kwame@example.com"} value={form.email} onChange={(e) => update("email", e.target.value)} />
                    </div>
                    <div>
                      <label className="label">Ghana Phone Number</label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-gray-400">🇬🇭</span>
                        <input type="tel" className="input pl-10" placeholder="024 000 0000" value={form.phone} onChange={(e) => update("phone", e.target.value)} />
                      </div>
                    </div>
                    <div>
                      <label className="label">Password</label>
                      <input type="password" className="input" placeholder="Min. 8 characters" value={form.password} onChange={(e) => update("password", e.target.value)} />
                    </div>
                    <button type="submit" disabled={isLoading} className="btn-primary w-full py-3 text-base mt-2">
                      {isLoading ? (
                        <span className="flex items-center justify-center gap-2">
                          <span className="h-4 w-4 animate-spin rounded-full border-2 border-gray-900/30 border-t-gray-900" />
                          Creating account...
                        </span>
                      ) : activeRole === "shipper" ? "Create Shipper Account" : "Create Courier Account"}
                    </button>
                  </form>
                  <p className="mt-5 text-center text-sm text-gray-500">
                    Already have an account?{" "}
                    <button onClick={() => switchAuthMode("login")} className="font-semibold text-brand-600 hover:text-brand-700 transition">Log in</button>
                  </p>
                  <p className="mt-3 text-center text-xs text-gray-400">
                    By signing up you agree to our{" "}
                    <span className="text-brand-600 cursor-pointer hover:underline">Terms</span>,{" "}
                    <span className="text-brand-600 cursor-pointer hover:underline">Privacy Policy</span>
                    {activeRole === "shipper" && (<>, and <span className="text-brand-600 cursor-pointer hover:underline">Escrow Agreement</span></>)}
                  </p>
                </>
              ) : (
                <>
                  <div className="mb-6">
                    <h3 className="text-lg font-bold text-gray-900">{activeRole === "shipper" ? "Shipper Log In" : "Courier Log In"}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {activeRole === "shipper" ? "Access your loads, bids, and shipment tracking" : "View available loads, manage bids, and track earnings"}
                    </p>
                  </div>
                  {error && (
                    <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-start gap-2">
                      <svg className="h-5 w-5 flex-shrink-0 mt-0.5 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                      </svg>
                      {error}
                    </div>
                  )}
                  <form onSubmit={handleLogin} className="space-y-4">
                    <div>
                      <label className="label">Email Address</label>
                      <input type="email" className="input" placeholder={activeRole === "shipper" ? "ama@enterprise.com" : "kwame@example.com"} value={loginEmail} onChange={(e) => { setLoginEmail(e.target.value); setError(""); }} />
                    </div>
                    <div>
                      <label className="label">Password</label>
                      <div className="relative">
                        <input type={showPassword ? "text" : "password"} className="input pr-10" placeholder="Enter your password" value={loginPassword} onChange={(e) => { setLoginPassword(e.target.value); setError(""); }} />
                        <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition">
                          {showPassword ? (
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
                          ) : (
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>
                          )}
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
                        <span className="text-sm text-gray-600">Remember me</span>
                      </label>
                      <button type="button" className="text-sm font-medium text-brand-600 hover:text-brand-700 transition">Forgot password?</button>
                    </div>
                    <button type="submit" disabled={isLoading} className="btn-purple w-full py-3 text-base">
                      {isLoading ? (
                        <span className="flex items-center justify-center gap-2">
                          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                          Signing in...
                        </span>
                      ) : "Sign In"}
                    </button>
                  </form>
                  <div className="relative mt-5">
                    <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200" /></div>
                    <div className="relative flex justify-center text-xs"><span className="bg-white px-3 text-gray-400">or</span></div>
                  </div>
                  <button className="mt-4 w-full flex items-center justify-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition">
                    <span>🇬🇭</span> Sign in with Phone Number (OTP)
                  </button>
                  <p className="mt-5 text-center text-sm text-gray-500">
                    Don&apos;t have an account?{" "}
                    <button onClick={() => switchAuthMode("signup")} className="font-semibold text-brand-600 hover:text-brand-700 transition">Sign up</button>
                  </p>
                </>
              )}
            </div>

            {/* Trust & Help */}
            <div className="mt-8 space-y-5">
              <p className="text-center text-sm text-gray-500">
                If you are unable to {authMode === "login" ? "login" : "sign up"}, please visit our{" "}
                <a href="mailto:support@loadmovegh.com" className="font-medium text-brand-600 hover:text-brand-700 underline underline-offset-2 transition">help centre</a>.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-5">
                <div className="flex items-center gap-2 rounded-full bg-green-50 border border-green-200 px-4 py-2">
                  <svg className="h-4 w-4 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" /></svg>
                  <span className="text-xs font-semibold text-green-700">SSL Secured</span>
                </div>
                <div className="flex items-center gap-2 rounded-full bg-brand-50 border border-brand-200 px-4 py-2">
                  <svg className="h-4 w-4 text-brand-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" /></svg>
                  <span className="text-xs font-semibold text-brand-700">Escrow Protected</span>
                </div>
                <div className="flex items-center gap-2 rounded-full bg-accent-50 border border-accent-200 px-4 py-2">
                  <span className="text-sm">🇬🇭</span>
                  <span className="text-xs font-semibold text-accent-700">MoMo Verified</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Features ─────────────────────────────────── */}
        <section className="py-16">
          <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl mb-12">Why LoadMoveGH?</h2>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { icon: <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09Z" />, title: "AI-Powered Pricing", desc: "Machine learning model trained on Ghana market data recommends fair bid prices for every route." },
              { icon: <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />, title: "Escrow Protection", desc: "Payments held securely via MTN Mobile Money escrow — released only after confirmed delivery." },
              { icon: <><path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" /></>, title: "Live GPS Tracking", desc: "Track your shipment in real-time from pickup to delivery across all 16 regions of Ghana." },
              { icon: <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />, title: "Smart Load Matching", desc: "AI matches couriers to loads based on proximity, reliability, vehicle suitability, and pricing." },
              { icon: <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286Zm0 13.036h.008v.008H12v-.008Z" />, title: "Fraud Detection", desc: "AI monitors every transaction for suspicious activity — fake companies, bid manipulation, and payment abuse." },
              { icon: <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 0 0 6 3.75v16.5a2.25 2.25 0 0 0 2.25 2.25h7.5A2.25 2.25 0 0 0 18 20.25V3.75a2.25 2.25 0 0 0-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3" />, title: "Mobile Money Native", desc: "Deposit, pay, and withdraw using MTN MoMo, Vodafone Cash, or AirtelTigo Money — no bank needed." },
            ].map((f) => (
              <div key={f.title} className="card-hover">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600 mb-4">
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">{f.icon}</svg>
                </div>
                <h3 className="text-base font-semibold text-gray-900">{f.title}</h3>
                <p className="mt-2 text-sm leading-6 text-gray-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Success Stories ───────────────────────────── */}
        <section className="py-16">
          <h2 className="text-center text-2xl font-bold text-gray-900 sm:text-3xl mb-12">Success Stories</h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { name: "Kwame Mensah", role: "Fleet Owner", company: "Mensah Haulage Ltd", subtitle: "Turning flexibility into growth with LM", image: "/stories/kwame.jpg", quote: "LM means we never have to say no to a customer.", highlight: "never have to say no", date: "07.11.2025" },
              { name: "Abena Osei-Bonsu", role: "Operations Manager", company: "GoldCoast Shipping", subtitle: "Celebrating 1 year on the Exchange", image: "/stories/abena.jpg", quote: "LM has opened a lot of doors for us.", highlight: "opened a lot of doors", date: "15.08.2025" },
              { name: "Yaw Asante", role: "Independent Courier", company: "Asante Logistics", subtitle: "Celebrating 5 years on the Exchange", image: "/stories/yaw.jpg", quote: "It'd be impossible to do it any other way.", highlight: "impossible", date: "15.04.2025" },
              { name: "Efua Darko", role: "CEO", company: "Darko Logistics Group", subtitle: "Celebrating 15 years on the Exchange", image: "/stories/efua.jpg", quote: "It's a perfect business model.", highlight: "perfect business model", date: "11.04.2025" },
            ].map((story) => (
              <div key={story.name} className="group rounded-2xl bg-brand-50 border border-brand-100 overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300">
                {/* Photo with quote overlay */}
                <div className="relative h-52 overflow-hidden">
                  <img src={story.image} alt={story.name} className="w-full h-full object-cover object-top" />
                  <div className="absolute inset-0 bg-gradient-to-t from-gray-900/80 via-gray-900/30 to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-4">
                    <p className="text-sm text-white/95 leading-snug italic">
                      &ldquo;{story.quote.split(story.highlight)[0]}
                      <span className="font-bold text-accent-300 not-italic">{story.highlight}</span>
                      {story.quote.split(story.highlight)[1]}&rdquo;
                    </p>
                  </div>
                </div>
                {/* Card body */}
                <div className="p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="inline-flex items-center rounded-full border border-brand-200 bg-white px-3 py-1 text-xs font-medium text-gray-600">Success stories</span>
                    <span className="text-xs text-gray-400">{story.date}</span>
                  </div>
                  <p className="text-sm font-semibold text-gray-900 leading-snug">{story.company}: {story.subtitle}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Bottom CTA ─────────────────────────────────── */}
        <section className="py-16 text-center">
          <div className="card bg-brand-700 text-white max-w-3xl mx-auto p-10 border-brand-600">
            <h2 className="text-2xl font-bold sm:text-3xl">Ready to move your freight?</h2>
            <p className="mt-3 text-brand-200 text-base">Join thousands of businesses and couriers across Ghana.</p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <button onClick={() => scrollToAuth("shipper", "signup")} className="inline-flex items-center justify-center rounded-full bg-accent-400 px-8 py-3 text-base font-bold text-gray-900 shadow-sm transition hover:bg-accent-500">
                Sign Up as Shipper
              </button>
              <button onClick={() => scrollToAuth("courier", "signup")} className="inline-flex items-center justify-center rounded-full bg-white/10 backdrop-blur-sm px-8 py-3 text-base font-bold text-white shadow-sm ring-1 ring-white/30 transition hover:bg-white/20">
                Sign Up as Courier
              </button>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ────────────────────────────────────── */}
      <footer className="bg-gray-900 text-gray-300">
        <div className="border-b border-gray-800">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <svg className="h-5 w-5 text-accent-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z" />
              </svg>
              <span className="text-lg sm:text-xl font-bold text-white">Call us +233 557 542 254</span>
            </div>
            <div className="flex items-center gap-3">
              {[
                { label: "Facebook", href: "https://facebook.com/loadmovegh", icon: <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" /> },
                { label: "Twitter / X", href: "https://x.com/loadmovegh", icon: <path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z" /> },
                { label: "LinkedIn", href: "https://linkedin.com/company/loadmovegh", icon: <><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" /><rect width="4" height="12" x="2" y="9" /><circle cx="4" cy="4" r="2" /></> },
                { label: "Instagram", href: "https://instagram.com/loadmovegh", icon: <><rect width="20" height="20" x="2" y="2" rx="5" ry="5" /><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" /><line x1="17.5" y1="6.5" x2="17.51" y2="6.5" /></> },
                { label: "YouTube", href: "https://youtube.com/@loadmovegh", icon: <><path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19.1c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z" /><polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02" /></> },
              ].map((s) => (
                <a key={s.label} href={s.href} target="_blank" rel="noopener noreferrer" aria-label={s.label}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-800 text-gray-400 hover:bg-brand-600 hover:text-white transition-all duration-200">
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">{s.icon}</svg>
                </a>
              ))}
            </div>
          </div>
        </div>
        <div className="border-b border-gray-800">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12 grid grid-cols-2 gap-8 sm:grid-cols-3 lg:grid-cols-6">
            {[
              { title: "Solutions", links: [["Courier drivers","/#auth"],["Shipping companies","/#auth"],["Freight forwarders","/#auth"],["Fleet owners","/#auth"]] },
              { title: "Platform", links: [["Driver App","/#auth"],["Fleet Manager","/#auth"],["AI Pricing Engine","/#auth"],["GPS Tracking","/#auth"]] },
              { title: "Resources", links: [["LM Academy","/#auth"],["Success stories","/#auth"],["Blog","/#auth"],["FAQs","/faqs"]] },
              { title: "Support", links: [["How to join","/#auth"],["Contact us","mailto:support@loadmovegh.com"],["Help centre","mailto:support@loadmovegh.com"]] },
              { title: "About", links: [["About us","/#auth"],["Our partners","/#auth"],["Careers","/#auth"]] },
              { title: "Legal", links: [["Privacy policy","/privacy"],["Terms of use","/terms"],["Cookie policy","/privacy#cookies"],["Data protection","/privacy"]] },
            ].map((col) => (
              <div key={col.title}>
                <h4 className="text-sm font-semibold text-white mb-4">{col.title}</h4>
                <ul className="space-y-2.5">
                  {col.links.map(([label, href]) => (
                    <li key={label}><a href={href} className="text-sm text-gray-400 hover:text-white transition">{label}</a></li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="border-b border-gray-800">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-5">
            <div className="flex flex-wrap justify-center gap-x-5 gap-y-2 text-xs text-gray-500">
              {["Courier loads Ghana","Freight jobs Accra","Truck driver jobs","Courier network Ghana","Owner driver jobs","Same day courier loads","Freight exchange","Haulage contracts","Logistics marketplace","Courier work for drivers"].map((kw) => (
                <a key={kw} href="/#auth" className="hover:text-gray-300 transition">{kw}</a>
              ))}
            </div>
          </div>
        </div>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="LoadMoveGH" width={36} height={36} className="h-8 w-auto object-contain" />
            <span className="text-sm font-bold text-white">LoadMove<span className="text-brand-400">GH</span></span>
          </div>
          <p className="text-xs text-gray-500">&copy; {new Date().getFullYear()} LoadMoveGH Ltd. All rights reserved. Built for Ghana&apos;s freight industry.</p>
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <svg className="h-3.5 w-3.5 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
            </svg>
            <span>SSL Secured</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
