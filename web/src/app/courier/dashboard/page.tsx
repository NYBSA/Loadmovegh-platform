"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { RequireAuth, useAuth } from "@/context/AuthContext";

/* ═══════════════════════════════════════════════════════════
   MOCK DATA
   ═══════════════════════════════════════════════════════════ */

const MOCK_LOADS = [
  { id: "L-1001", title: "Electronics — Accra to Kumasi", origin: "Accra", destination: "Kumasi", distance: 252, weight: 800, vehicle: "Box Truck", price: 1200, urgency: "standard", cargo: "Electronics", status: "active", bids: 3, posted: "2h ago" },
  { id: "L-1002", title: "Perishables — Tema to Takoradi", origin: "Tema", destination: "Takoradi", distance: 225, weight: 1500, vehicle: "Refrigerated", price: 2400, urgency: "urgent", cargo: "Perishables", status: "active", bids: 7, posted: "45m ago" },
  { id: "L-1003", title: "Furniture — Cape Coast to Ho", origin: "Cape Coast", destination: "Ho", distance: 230, weight: 3200, vehicle: "Flatbed", price: 1800, urgency: "express", cargo: "Furniture", status: "active", bids: 1, posted: "5h ago" },
  { id: "L-1004", title: "Medical Supplies — Tamale to Wa", origin: "Tamale", destination: "Wa", distance: 300, weight: 400, vehicle: "Van", price: 900, urgency: "urgent", cargo: "Medical", status: "active", bids: 5, posted: "1h ago" },
  { id: "L-1005", title: "Construction — Kumasi to Sunyani", origin: "Kumasi", destination: "Sunyani", distance: 130, weight: 12000, vehicle: "Heavy Truck", price: 3500, urgency: "standard", cargo: "Construction", status: "active", bids: 2, posted: "3h ago" },
  { id: "L-1006", title: "Textiles — Accra to Tamale", origin: "Accra", destination: "Tamale", distance: 604, weight: 2000, vehicle: "Box Truck", price: 4200, urgency: "standard", cargo: "Textiles", status: "active", bids: 4, posted: "6h ago" },
];

const MOCK_NOTIFICATIONS = [
  { id: 1, text: "Your bid on L-1001 was accepted!", type: "success", time: "10m ago" },
  { id: 2, text: "New urgent load posted on Tema–Takoradi route", type: "info", time: "45m ago" },
  { id: 3, text: "Payment of GHS 1,140 released to your wallet", type: "success", time: "2h ago" },
  { id: 4, text: "Bid on L-0998 was outbid by another courier", type: "warning", time: "4h ago" },
];

const EARNINGS_DATA = [
  { month: "Sep", amount: 4200 },
  { month: "Oct", amount: 5800 },
  { month: "Nov", amount: 4900 },
  { month: "Dec", amount: 7200 },
  { month: "Jan", amount: 6400 },
  { month: "Feb", amount: 3100 },
];

const REGIONS = ["All Regions", "Greater Accra", "Ashanti", "Western", "Northern", "Volta", "Eastern", "Central", "Upper East", "Upper West", "Bono"];
const VEHICLES = ["All Vehicles", "Van", "Box Truck", "Flatbed", "Refrigerated", "Heavy Truck", "Motorcycle"];
const URGENCY_OPTIONS = ["All", "Standard", "Express", "Urgent"];

/* ═══════════════════════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════════════════════ */

export default function CourierDashboardPage() {
  return (
    <RequireAuth role="courier">
      <CourierDashboard />
    </RequireAuth>
  );
}

function CourierDashboard() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [region, setRegion] = useState("All Regions");
  const [vehicle, setVehicle] = useState("All Vehicles");
  const [urgency, setUrgency] = useState("All");
  const [priceRange, setPriceRange] = useState([0, 10000]);
  const [showBidModal, setShowBidModal] = useState(false);
  const [selectedLoad, setSelectedLoad] = useState<(typeof MOCK_LOADS)[0] | null>(null);
  const [bidAmount, setBidAmount] = useState("");
  const [bidMessage, setBidMessage] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);

  const initials = user?.fullName
    ? user.fullName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "AK";

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const filteredLoads = MOCK_LOADS.filter((l) => {
    if (search && !l.title.toLowerCase().includes(search.toLowerCase()) && !l.origin.toLowerCase().includes(search.toLowerCase()) && !l.destination.toLowerCase().includes(search.toLowerCase())) return false;
    if (region !== "All Regions" && l.origin !== region && l.destination !== region) return false;
    if (vehicle !== "All Vehicles" && l.vehicle !== vehicle) return false;
    if (urgency !== "All" && l.urgency !== urgency.toLowerCase()) return false;
    if (l.price < priceRange[0] || l.price > priceRange[1]) return false;
    return true;
  });

  const openBidModal = (load: (typeof MOCK_LOADS)[0]) => {
    setSelectedLoad(load);
    setBidAmount(String(Math.round(load.price * 0.95)));
    setBidMessage("");
    setShowBidModal(true);
  };

  const maxEarning = Math.max(...EARNINGS_DATA.map((e) => e.amount));

  const urgencyColor = (u: string) => {
    if (u === "urgent") return "badge-red";
    if (u === "express") return "badge-yellow";
    return "badge-gray";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Top Nav ────────────────────────────────────── */}
      <nav className="border-b border-gray-200 bg-white sticky top-0 z-40">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-14 items-center justify-between">
            <div className="flex items-center gap-3">
              <Link href="/" className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-brand-600 flex items-center justify-center">
                  <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 0 1-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 0 1-3 0m3 0a1.5 1.5 0 0 0-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 0 0-3.213-9.193 2.056 2.056 0 0 0-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 0 0-10.026 0 1.106 1.106 0 0 0-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" /></svg>
                </div>
                <span className="font-bold text-gray-900">LoadMove<span className="text-brand-600">GH</span></span>
              </Link>
              <span className="badge-blue">Courier</span>
            </div>
            <div className="flex items-center gap-3">
              {/* Notification bell */}
              <button onClick={() => setShowNotifications(!showNotifications)} className="relative p-2 text-gray-500 hover:text-gray-700 transition">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" /></svg>
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
              </button>
              <div className="h-8 w-8 rounded-full bg-brand-100 flex items-center justify-center text-sm font-semibold text-brand-700">{initials}</div>
              <button onClick={handleLogout} className="text-xs text-gray-500 hover:text-red-600 font-medium transition" title="Log out">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" /></svg>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
        {/* ── Stats Row ───────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[
            { label: "Wallet Balance", value: "GHS 3,240.00", sub: "Available", color: "text-brand-700" },
            { label: "Active Bids", value: "4", sub: "2 pending review", color: "text-amber-600" },
            { label: "Trips This Month", value: "12", sub: "94% on-time", color: "text-blue-600" },
            { label: "Rating", value: "4.8 / 5.0", sub: "127 ratings", color: "text-purple-600" },
          ].map((s) => (
            <div key={s.label} className="card">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{s.label}</p>
              <p className={`mt-1 text-xl font-bold ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-400 mt-0.5">{s.sub}</p>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* ── Left Column: Loads Board ──────────────── */}
          <div className="lg:col-span-2 space-y-4">
            {/* Filters */}
            <div className="card">
              <div className="flex flex-col sm:flex-row gap-3">
                <input type="text" placeholder="Search loads..." value={search} onChange={(e) => setSearch(e.target.value)} className="input flex-1" />
                <select value={region} onChange={(e) => setRegion(e.target.value)} className="input sm:w-40">
                  {REGIONS.map((r) => <option key={r}>{r}</option>)}
                </select>
                <select value={vehicle} onChange={(e) => setVehicle(e.target.value)} className="input sm:w-40">
                  {VEHICLES.map((v) => <option key={v}>{v}</option>)}
                </select>
                <select value={urgency} onChange={(e) => setUrgency(e.target.value)} className="input sm:w-32">
                  {URGENCY_OPTIONS.map((u) => <option key={u}>{u}</option>)}
                </select>
              </div>
              <div className="mt-3 flex items-center gap-3 text-xs text-gray-500">
                <span>Price: GHS {priceRange[0].toLocaleString()} – {priceRange[1].toLocaleString()}</span>
                <input type="range" min={0} max={10000} step={100} value={priceRange[1]} onChange={(e) => setPriceRange([priceRange[0], Number(e.target.value)])} className="flex-1 accent-brand-600" />
              </div>
            </div>

            {/* Load Cards */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-700">Available Loads ({filteredLoads.length})</h2>
              </div>
              {filteredLoads.length === 0 && (
                <div className="card text-center py-12 text-gray-400">No loads match your filters.</div>
              )}
              {filteredLoads.map((load) => (
                <div key={load.id} className="card-hover">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-semibold text-gray-900 truncate">{load.title}</h3>
                        <span className={urgencyColor(load.urgency)}>{load.urgency}</span>
                      </div>
                      <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
                        <span>{load.origin} → {load.destination}</span>
                        <span>{load.distance} km</span>
                        <span>{load.weight.toLocaleString()} kg</span>
                        <span>{load.vehicle}</span>
                        <span>{load.bids} bid{load.bids !== 1 ? "s" : ""}</span>
                        <span>{load.posted}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right">
                        <p className="text-lg font-bold text-brand-700">GHS {load.price.toLocaleString()}</p>
                        <p className="text-[11px] text-gray-400">Shipper budget</p>
                      </div>
                      <button onClick={() => openBidModal(load)} className="btn-primary text-xs px-3 py-2">
                        Place Bid
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Right Column: Sidebar ────────────────── */}
          <div className="space-y-4">
            {/* Map Placeholder */}
            <div className="card overflow-hidden">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Load Map</h3>
              <div className="h-48 rounded-lg bg-gradient-to-br from-brand-50 to-emerald-50 flex items-center justify-center border border-dashed border-brand-200">
                <div className="text-center">
                  <svg className="h-8 w-8 text-brand-300 mx-auto" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" /></svg>
                  <p className="mt-2 text-xs text-brand-400">Interactive map</p>
                  <p className="text-[10px] text-gray-400">Connect Google Maps API</p>
                </div>
              </div>
            </div>

            {/* Earnings Chart */}
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Earnings (6 months)</h3>
              <div className="flex items-end gap-2 h-32">
                {EARNINGS_DATA.map((e) => (
                  <div key={e.month} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[10px] text-gray-500">{(e.amount / 1000).toFixed(1)}k</span>
                    <div
                      className="w-full rounded-t bg-brand-500 transition-all"
                      style={{ height: `${(e.amount / maxEarning) * 100}%` }}
                    />
                    <span className="text-[10px] text-gray-400">{e.month}</span>
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between text-xs">
                <span className="text-gray-500">Total earned</span>
                <span className="font-semibold text-gray-700">GHS {EARNINGS_DATA.reduce((a, b) => a + b.amount, 0).toLocaleString()}</span>
              </div>
            </div>

            {/* Notifications */}
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Notifications</h3>
              <div className="space-y-2.5">
                {MOCK_NOTIFICATIONS.map((n) => (
                  <div key={n.id} className="flex gap-2.5 items-start">
                    <div className={`mt-0.5 h-2 w-2 rounded-full shrink-0 ${n.type === "success" ? "bg-emerald-500" : n.type === "warning" ? "bg-amber-500" : "bg-blue-500"}`} />
                    <div className="min-w-0">
                      <p className="text-xs text-gray-700 leading-relaxed">{n.text}</p>
                      <p className="text-[10px] text-gray-400 mt-0.5">{n.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Bid Modal ────────────────────────────────── */}
      {showBidModal && selectedLoad && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">Place a Bid</h3>
              <button onClick={() => setShowBidModal(false)} className="text-gray-400 hover:text-gray-600 transition">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <div className="mb-4 p-3 rounded-lg bg-gray-50">
              <p className="text-sm font-medium text-gray-900">{selectedLoad.title}</p>
              <p className="text-xs text-gray-500 mt-1">{selectedLoad.origin} → {selectedLoad.destination} &middot; {selectedLoad.distance} km &middot; {selectedLoad.weight.toLocaleString()} kg</p>
              <p className="text-sm font-semibold text-brand-600 mt-2">Shipper budget: GHS {selectedLoad.price.toLocaleString()}</p>
            </div>
            <div className="space-y-3">
              <div>
                <label className="label">Your Bid (GHS)</label>
                <input type="number" value={bidAmount} onChange={(e) => setBidAmount(e.target.value)} className="input" placeholder="Enter your price" />
              </div>
              <div>
                <label className="label">Message (optional)</label>
                <textarea value={bidMessage} onChange={(e) => setBidMessage(e.target.value)} className="input h-20 resize-none" placeholder="Why should the shipper pick you?" />
              </div>
            </div>
            <div className="mt-5 flex gap-3">
              <button onClick={() => setShowBidModal(false)} className="btn-secondary flex-1">Cancel</button>
              <button onClick={() => { setShowBidModal(false); }} className="btn-primary flex-1">Submit Bid</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
