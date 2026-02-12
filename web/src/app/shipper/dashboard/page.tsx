"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { RequireAuth, useAuth } from "@/context/AuthContext";

/* ═══════════════════════════════════════════════════════════
   MOCK DATA
   ═══════════════════════════════════════════════════════════ */

const MOCK_MY_LOADS = [
  { id: "L-2001", title: "Electronics to Kumasi", origin: "Accra", destination: "Kumasi", weight: 800, price: 1200, status: "bidding", bids: 5, created: "2h ago" },
  { id: "L-2002", title: "Perishables to Takoradi", origin: "Tema", destination: "Takoradi", weight: 1500, price: 2400, status: "assigned", bids: 3, created: "1d ago", courier: "Kwame Asante" },
  { id: "L-2003", title: "Medical to Tamale", origin: "Accra", destination: "Tamale", weight: 400, price: 3200, status: "in_transit", bids: 7, created: "2d ago", courier: "Ama Serwaa" },
  { id: "L-2004", title: "Furniture to Cape Coast", origin: "Kumasi", destination: "Cape Coast", weight: 3200, price: 1800, status: "delivered", bids: 4, created: "5d ago", courier: "Kofi Mensah" },
  { id: "L-2005", title: "Textiles to Ho", origin: "Accra", destination: "Ho", weight: 600, price: 950, status: "completed", bids: 2, created: "8d ago", courier: "Yaa Amoako" },
];

const MOCK_BIDS = [
  { id: "B-301", courier: "Kwame Asante", price: 1100, eta: "8 hours", rating: 4.9, trips: 87, message: "I have a refrigerated truck, can pick up today.", status: "pending" },
  { id: "B-302", courier: "Ama Serwaa", price: 1150, eta: "10 hours", rating: 4.7, trips: 52, message: "Available immediately, GPS tracked vehicle.", status: "pending" },
  { id: "B-303", courier: "Kofi Mensah", price: 1250, eta: "7 hours", rating: 4.5, trips: 34, message: "Express delivery, insured cargo.", status: "pending" },
  { id: "B-304", courier: "Yaa Amoako", price: 1080, eta: "12 hours", rating: 4.8, trips: 120, message: "Most competitive price, reliable service.", status: "pending" },
  { id: "B-305", courier: "Nana Ofori", price: 1300, eta: "6 hours", rating: 4.6, trips: 65, message: "Fastest route, experienced driver.", status: "pending" },
];

const MOCK_TRACKING = [
  { time: "09:15 AM", event: "Picked up from Tema Port warehouse", location: "Tema" },
  { time: "10:30 AM", event: "Passed Accra toll booth, heading west", location: "Accra" },
  { time: "12:45 PM", event: "Rest stop at Saltpond", location: "Saltpond" },
  { time: "02:10 PM", event: "In transit — estimated 1.5h to destination", location: "En route" },
];

const MOCK_INVOICES = [
  { id: "INV-001", load: "L-2005", amount: 950, status: "paid", date: "Feb 4, 2026", courier: "Yaa Amoako" },
  { id: "INV-002", load: "L-2004", amount: 1800, status: "paid", date: "Feb 7, 2026", courier: "Kofi Mensah" },
  { id: "INV-003", load: "L-2003", amount: 3200, status: "in_escrow", date: "Feb 10, 2026", courier: "Ama Serwaa" },
  { id: "INV-004", load: "L-2002", amount: 2400, status: "in_escrow", date: "Feb 11, 2026", courier: "Kwame Asante" },
];

const CARGO_TYPES = ["Electronics", "Perishables", "Furniture", "Textiles", "Construction", "Medical", "Chemicals", "Livestock", "General"];
const VEHICLE_TYPES = ["Any", "Van", "Box Truck", "Flatbed", "Refrigerated", "Heavy Truck", "Motorcycle"];
const URGENCY_OPTIONS = ["Standard", "Express", "Urgent"];

/* ═══════════════════════════════════════════════════════════
   COMPONENT
   ═══════════════════════════════════════════════════════════ */

type Tab = "loads" | "post" | "bids" | "tracking" | "invoices";

export default function ShipperDashboardPage() {
  return (
    <RequireAuth role="shipper">
      <ShipperDashboard />
    </RequireAuth>
  );
}

function ShipperDashboard() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("loads");
  const [selectedLoadForBids, setSelectedLoadForBids] = useState<string | null>("L-2001");

  const initials = user?.fullName
    ? user.fullName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "EO";

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  const statusColor = (s: string) => {
    const map: Record<string, string> = {
      bidding: "badge-blue", assigned: "badge-yellow", in_transit: "badge-yellow",
      delivered: "badge-green", completed: "badge-green", cancelled: "badge-red", draft: "badge-gray",
    };
    return map[s] || "badge-gray";
  };

  const invoiceStatusColor = (s: string) => {
    if (s === "paid") return "badge-green";
    if (s === "in_escrow") return "badge-yellow";
    return "badge-gray";
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "loads", label: "My Loads" },
    { key: "post", label: "Post Load" },
    { key: "bids", label: "View Bids" },
    { key: "tracking", label: "Tracking" },
    { key: "invoices", label: "Invoices" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Nav ────────────────────────────────────────── */}
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
              <span className="badge-green">Shipper</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-500 hidden sm:block">Wallet: <span className="font-semibold text-gray-700">GHS 8,450.00</span></span>
              <div className="h-8 w-8 rounded-full bg-brand-100 flex items-center justify-center text-sm font-semibold text-brand-700">{initials}</div>
              <button onClick={handleLogout} className="text-xs text-gray-500 hover:text-red-600 font-medium transition" title="Log out">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" /></svg>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
        {/* ── Stats ─────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[
            { label: "Active Loads", value: "3", color: "text-blue-600" },
            { label: "In Escrow", value: "GHS 5,600", color: "text-amber-600" },
            { label: "Completed", value: "24", color: "text-emerald-600" },
            { label: "Total Spent", value: "GHS 42,800", color: "text-purple-600" },
          ].map((s) => (
            <div key={s.label} className="card">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{s.label}</p>
              <p className={`mt-1 text-xl font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* ── Tabs ──────────────────────────────────────── */}
        <div className="flex gap-1 border-b border-gray-200 mb-6 overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition ${tab === t.key ? "border-brand-600 text-brand-700" : "border-transparent text-gray-500 hover:text-gray-700"}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* ── My Loads ─────────────────────────────────── */}
        {tab === "loads" && (
          <div className="space-y-3">
            {MOCK_MY_LOADS.map((l) => (
              <div key={l.id} className="card-hover">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-sm font-semibold text-gray-900">{l.title}</h3>
                      <span className={statusColor(l.status)}>{l.status.replace("_", " ")}</span>
                      <span className="text-[10px] text-gray-400">{l.id}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{l.origin} → {l.destination} &middot; {l.weight.toLocaleString()} kg &middot; {l.bids} bids &middot; {l.created}</p>
                    {l.courier && <p className="text-xs text-brand-600 mt-0.5">Courier: {l.courier}</p>}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <p className="text-lg font-bold text-gray-900">GHS {l.price.toLocaleString()}</p>
                    {l.status === "bidding" && (
                      <button onClick={() => { setSelectedLoadForBids(l.id); setTab("bids"); }} className="btn-primary text-xs px-3 py-2">View Bids</button>
                    )}
                    {l.status === "in_transit" && (
                      <button onClick={() => setTab("tracking")} className="btn-secondary text-xs px-3 py-2">Track</button>
                    )}
                    {l.status === "delivered" && (
                      <button className="btn-primary text-xs px-3 py-2">Confirm</button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Post Load ───────────────────────────────── */}
        {tab === "post" && (
          <div className="max-w-2xl">
            <div className="card">
              <h2 className="text-lg font-bold text-gray-900 mb-5">Post a New Load</h2>
              <div className="space-y-4">
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Pickup City</label>
                    <input className="input" placeholder="e.g. Accra" />
                  </div>
                  <div>
                    <label className="label">Delivery City</label>
                    <input className="input" placeholder="e.g. Kumasi" />
                  </div>
                </div>
                <div>
                  <label className="label">Load Title</label>
                  <input className="input" placeholder="e.g. Electronics shipment to Kumasi" />
                </div>
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="label">Cargo Type</label>
                    <select className="input">{CARGO_TYPES.map((c) => <option key={c}>{c}</option>)}</select>
                  </div>
                  <div>
                    <label className="label">Vehicle Type</label>
                    <select className="input">{VEHICLE_TYPES.map((v) => <option key={v}>{v}</option>)}</select>
                  </div>
                </div>
                <div className="grid sm:grid-cols-3 gap-4">
                  <div>
                    <label className="label">Weight (kg)</label>
                    <input type="number" className="input" placeholder="0" />
                  </div>
                  <div>
                    <label className="label">Budget (GHS)</label>
                    <input type="number" className="input" placeholder="0.00" />
                  </div>
                  <div>
                    <label className="label">Urgency</label>
                    <select className="input">{URGENCY_OPTIONS.map((u) => <option key={u}>{u}</option>)}</select>
                  </div>
                </div>
                <div>
                  <label className="label">Special Instructions</label>
                  <textarea className="input h-20 resize-none" placeholder="Fragile items, loading dock access, etc." />
                </div>
                <div className="pt-2">
                  <button className="btn-primary w-full sm:w-auto">Post Load</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── View Bids ───────────────────────────────── */}
        {tab === "bids" && (
          <div>
            <div className="flex items-center gap-3 mb-4">
              <h2 className="text-sm font-semibold text-gray-700">Bids for {selectedLoadForBids}</h2>
              <span className="badge-blue">{MOCK_BIDS.length} bids</span>
            </div>
            <div className="space-y-3">
              {MOCK_BIDS.map((b) => (
                <div key={b.id} className="card-hover">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <div className="h-9 w-9 rounded-full bg-brand-100 flex items-center justify-center text-sm font-semibold text-brand-700">{b.courier.split(" ").map(n => n[0]).join("")}</div>
                        <div>
                          <p className="text-sm font-semibold text-gray-900">{b.courier}</p>
                          <p className="text-xs text-gray-500">
                            <span className="text-amber-500">&#9733;</span> {b.rating} &middot; {b.trips} trips
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-gray-600 mt-2 italic">&ldquo;{b.message}&rdquo;</p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right">
                        <p className="text-lg font-bold text-brand-700">GHS {b.price.toLocaleString()}</p>
                        <p className="text-[11px] text-gray-400">ETA: {b.eta}</p>
                      </div>
                      <div className="flex gap-2">
                        <button className="btn-primary text-xs px-3 py-2">Accept</button>
                        <button className="btn-secondary text-xs px-3 py-2">Reject</button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Tracking ────────────────────────────────── */}
        {tab === "tracking" && (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Shipment: L-2003 — Medical to Tamale</h2>
              <div className="flex items-center gap-3 mb-4">
                <span className="badge-yellow">In Transit</span>
                <span className="text-xs text-gray-500">Courier: Ama Serwaa</span>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-gray-100 rounded-full h-2 mb-6">
                <div className="bg-brand-500 h-2 rounded-full" style={{ width: "65%" }} />
              </div>
              {/* Timeline */}
              <div className="space-y-4">
                {MOCK_TRACKING.map((t, i) => (
                  <div key={i} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className={`h-3 w-3 rounded-full ${i === MOCK_TRACKING.length - 1 ? "bg-brand-500 ring-4 ring-brand-100" : "bg-gray-300"}`} />
                      {i < MOCK_TRACKING.length - 1 && <div className="w-px h-full bg-gray-200 mt-1" />}
                    </div>
                    <div className="pb-4">
                      <p className="text-xs font-medium text-gray-900">{t.event}</p>
                      <p className="text-[11px] text-gray-400">{t.time} &middot; {t.location}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Live Map</h3>
              <div className="h-80 rounded-lg bg-gradient-to-br from-brand-50 to-emerald-50 flex items-center justify-center border border-dashed border-brand-200">
                <div className="text-center">
                  <svg className="h-10 w-10 text-brand-300 mx-auto" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" /></svg>
                  <p className="mt-2 text-xs text-brand-400">Real-time GPS tracking</p>
                  <p className="text-[10px] text-gray-400">Connect Google Maps API</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Invoices ────────────────────────────────── */}
        {tab === "invoices" && (
          <div className="card overflow-hidden">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Payment History</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase">Invoice</th>
                    <th className="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase">Load</th>
                    <th className="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase">Courier</th>
                    <th className="text-right py-2.5 px-3 text-xs font-medium text-gray-500 uppercase">Amount</th>
                    <th className="text-center py-2.5 px-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="text-left py-2.5 px-3 text-xs font-medium text-gray-500 uppercase">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {MOCK_INVOICES.map((inv) => (
                    <tr key={inv.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition">
                      <td className="py-3 px-3 font-medium text-gray-900">{inv.id}</td>
                      <td className="py-3 px-3 text-gray-600">{inv.load}</td>
                      <td className="py-3 px-3 text-gray-600">{inv.courier}</td>
                      <td className="py-3 px-3 text-right font-semibold text-gray-900">GHS {inv.amount.toLocaleString()}</td>
                      <td className="py-3 px-3 text-center"><span className={invoiceStatusColor(inv.status)}>{inv.status.replace("_", " ")}</span></td>
                      <td className="py-3 px-3 text-gray-500">{inv.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
