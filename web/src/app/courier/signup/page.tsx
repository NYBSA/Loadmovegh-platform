"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const VEHICLE_TYPES = [
  "Motorcycle Truck",
  "Small Van",
  "Big Van",
  "Flatbed",
  "Box Truck",
  "Container Truck",
  "Refrigerated",
  "Tipper",
  "Heavy Truck",
];

const GHANA_REGIONS = [
  "Greater Accra",
  "Ashanti",
  "Western",
  "Central",
  "Eastern",
  "Volta",
  "Northern",
  "Upper East",
  "Upper West",
  "Bono",
  "Bono East",
  "Ahafo",
  "Savannah",
  "North East",
  "Oti",
  "Western North",
];

export default function CourierSignupPage() {
  const { signup, isLoading } = useAuth();
  const router = useRouter();

  const [form, setForm] = useState({
    fullName: "",
    email: "",
    phone: "",
    vehicleType: "",
    region: "",
    password: "",
    confirmPassword: "",
    agreeTerms: false,
  });
  const [error, setError] = useState("");
  const [step, setStep] = useState(1); // 1 = personal, 2 = vehicle & password

  function update(field: string, value: string | boolean) {
    setForm((f) => ({ ...f, [field]: value }));
    setError("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (step === 1) {
      if (!form.fullName || !form.email || !form.phone) {
        setError("Please fill in all fields");
        return;
      }
      if (!/^\+?233\s?\d{2}\s?\d{3}\s?\d{4}$/.test(form.phone.replace(/\s/g, "")) && !/^0\d{9}$/.test(form.phone.replace(/\s/g, ""))) {
        setError("Enter a valid Ghana phone number (e.g. 024 000 0000)");
        return;
      }
      setStep(2);
      return;
    }

    /* Step 2 validation */
    if (!form.vehicleType) {
      setError("Select your vehicle type");
      return;
    }
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (!form.agreeTerms) {
      setError("You must agree to the Terms of Service");
      return;
    }

    try {
      await signup({
        fullName: form.fullName,
        email: form.email,
        phone: form.phone,
        password: form.password,
        role: "courier",
        vehicleType: form.vehicleType,
      });
      router.push("/courier/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Signup failed. Try again.");
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* ── Left Panel — Branding ──────────────────────── */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-brand-700 via-brand-600 to-emerald-700 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 -left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-emerald-300 rounded-full blur-3xl" />
        </div>
        <div className="relative z-10 flex flex-col justify-center px-12 lg:px-16">
          <Link href="/" className="flex items-center gap-2 mb-12">
            <div className="h-10 w-10 rounded-lg bg-white/20 backdrop-blur flex items-center justify-center">
              <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 0 1-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 0 0-3.213-9.193 2.056 2.056 0 0 0-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 0 0-10.026 0 1.106 1.106 0 0 0-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
              </svg>
            </div>
            <span className="text-xl font-bold text-white">LoadMoveGH</span>
          </Link>

          <h2 className="text-3xl lg:text-4xl font-extrabold text-white leading-tight">
            Start earning with <br />every delivery
          </h2>
          <p className="mt-4 text-brand-100 text-lg max-w-md">
            Join 3,200+ verified couriers moving freight across all 16 regions
            of Ghana. Get matched to loads, bid competitively, and get paid via
            Mobile Money.
          </p>

          {/* Trust badges */}
          <div className="mt-10 grid grid-cols-2 gap-4">
            {[
              { stat: "GHS 8.2M+", label: "Paid to couriers" },
              { stat: "12,400+", label: "Loads completed" },
              { stat: "4.8★", label: "Avg. courier rating" },
              { stat: "< 2 hrs", label: "Average match time" },
            ].map((b) => (
              <div key={b.label} className="bg-white/10 backdrop-blur rounded-lg p-3">
                <p className="text-lg font-bold text-white">{b.stat}</p>
                <p className="text-xs text-brand-200">{b.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right Panel — Form ─────────────────────────── */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-8 py-12 bg-gray-50">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="h-9 w-9 rounded-lg bg-brand-600 flex items-center justify-center">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 0 1-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 0 0-3.213-9.193 2.056 2.056 0 0 0-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 0 0-10.026 0 1.106 1.106 0 0 0-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
              </svg>
            </div>
            <span className="text-xl font-bold text-gray-900">
              LoadMove<span className="text-brand-600">GH</span>
            </span>
          </div>

          {/* Steps indicator */}
          <div className="flex items-center gap-3 mb-6">
            <div className={`flex items-center gap-2 ${step >= 1 ? "text-brand-600" : "text-gray-400"}`}>
              <span className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold ${step >= 1 ? "bg-brand-600 text-white" : "bg-gray-200 text-gray-500"}`}>1</span>
              <span className="text-sm font-medium">Personal Info</span>
            </div>
            <div className="flex-1 h-px bg-gray-300" />
            <div className={`flex items-center gap-2 ${step >= 2 ? "text-brand-600" : "text-gray-400"}`}>
              <span className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold ${step >= 2 ? "bg-brand-600 text-white" : "bg-gray-200 text-gray-500"}`}>2</span>
              <span className="text-sm font-medium">Vehicle & Security</span>
            </div>
          </div>

          <h1 className="text-2xl font-bold text-gray-900">Create courier account</h1>
          <p className="mt-1 text-sm text-gray-500">
            {step === 1
              ? "Tell us about yourself"
              : "Set up your vehicle and password"}
          </p>

          {error && (
            <div className="mt-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-start gap-2">
              <svg className="h-5 w-5 flex-shrink-0 mt-0.5 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {step === 1 ? (
              <>
                <div>
                  <label className="label">Full Name</label>
                  <input type="text" className="input" placeholder="Kwame Asante" value={form.fullName} onChange={(e) => update("fullName", e.target.value)} />
                </div>
                <div>
                  <label className="label">Email Address</label>
                  <input type="email" className="input" placeholder="kwame@example.com" value={form.email} onChange={(e) => update("email", e.target.value)} />
                </div>
                <div>
                  <label className="label">Ghana Phone Number</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-gray-400">🇬🇭</span>
                    <input type="tel" className="input pl-10" placeholder="024 000 0000" value={form.phone} onChange={(e) => update("phone", e.target.value)} />
                  </div>
                </div>
                <div>
                  <label className="label">Primary Region</label>
                  <select className="input" value={form.region} onChange={(e) => update("region", e.target.value)}>
                    <option value="">Select region</option>
                    {GHANA_REGIONS.map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="label">Vehicle Type</label>
                  <div className="grid grid-cols-3 gap-2">
                    {VEHICLE_TYPES.map((vt) => (
                      <button
                        key={vt}
                        type="button"
                        onClick={() => update("vehicleType", vt)}
                        className={`rounded-lg border px-3 py-2 text-xs font-medium transition ${
                          form.vehicleType === vt
                            ? "border-brand-600 bg-brand-50 text-brand-700 ring-1 ring-brand-600"
                            : "border-gray-200 bg-white text-gray-600 hover:border-gray-300"
                        }`}
                      >
                        {vt}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="label">Password</label>
                  <input type="password" className="input" placeholder="Min. 8 characters" value={form.password} onChange={(e) => update("password", e.target.value)} />
                </div>
                <div>
                  <label className="label">Confirm Password</label>
                  <input type="password" className="input" placeholder="Re-enter password" value={form.confirmPassword} onChange={(e) => update("confirmPassword", e.target.value)} />
                </div>
                <label className="flex items-start gap-2 mt-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.agreeTerms}
                    onChange={(e) => update("agreeTerms", e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                  />
                  <span className="text-xs text-gray-500">
                    I agree to the{" "}
                    <span className="text-brand-600 hover:underline cursor-pointer">Terms of Service</span>{" "}
                    and{" "}
                    <span className="text-brand-600 hover:underline cursor-pointer">Privacy Policy</span>
                  </span>
                </label>
              </>
            )}

            <div className="flex gap-3 pt-2">
              {step === 2 && (
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="btn-secondary flex-1"
                >
                  Back
                </button>
              )}
              <button
                type="submit"
                disabled={isLoading}
                className="btn-primary flex-1 py-3"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Creating account...
                  </span>
                ) : step === 1 ? (
                  "Continue"
                ) : (
                  "Create Account"
                )}
              </button>
            </div>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{" "}
            <Link href="/courier/login" className="font-semibold text-brand-600 hover:text-brand-700 transition">
              Log in
            </Link>
          </p>

          <p className="mt-3 text-center text-xs text-gray-400">
            Are you a shipper?{" "}
            <Link href="/shipper/signup" className="text-brand-600 hover:underline">
              Sign up as a shipper instead
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
