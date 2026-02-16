"use client";

import { useState } from "react";
import AdminLayout from "@/components/AdminLayout";
import { useAdmin } from "@/context/AdminContext";

/* ═══════════════════════════════════════════════════════════════
   MOCK DATA — OVERVIEW
   ═══════════════════════════════════════════════════════════════ */

const KPI = [
  { label: "Total Revenue", value: "GHS 2.84M", delta: "+12.3%", up: true, sub: "Last 30 days" },
  { label: "Active Users", value: "4,812", delta: "+8.1%", up: true, sub: "Shippers + Couriers" },
  { label: "Loads This Month", value: "1,247", delta: "+15.6%", up: true, sub: "vs 1,079 last month" },
  { label: "Platform Commission", value: "GHS 142K", delta: "+11.9%", up: true, sub: "5% avg rate" },
  { label: "Open Disputes", value: "23", delta: "-4.2%", up: false, sub: "18 under review" },
  { label: "Fraud Alerts", value: "7", delta: "+2", up: true, sub: "3 critical" },
];

const REVENUE_MONTHLY = [
  { month: "Sep", revenue: 198000, commission: 9900 },
  { month: "Oct", revenue: 245000, commission: 12250 },
  { month: "Nov", revenue: 212000, commission: 10600 },
  { month: "Dec", revenue: 312000, commission: 15600 },
  { month: "Jan", revenue: 289000, commission: 14450 },
  { month: "Feb", revenue: 284000, commission: 14200 },
];

const LOAD_VOLUME = [
  { month: "Sep", count: 824 },
  { month: "Oct", count: 1012 },
  { month: "Nov", count: 879 },
  { month: "Dec", count: 1198 },
  { month: "Jan", count: 1079 },
  { month: "Feb", count: 1247 },
];

/* ═══════════════════════════════════════════════════════════════
   MOCK DATA — USER APPROVALS
   ═══════════════════════════════════════════════════════════════ */

const PENDING_USERS = [
  { id: "U-401", name: "Kofi Transport Ltd", email: "info@kofitransport.gh", type: "courier", phone: "+233 24 555 1234", kyc: "pending", regNum: "GH-2026-4481", submitted: "2h ago", docs: 3 },
  { id: "U-402", name: "Ama Logistics", email: "ama@amalogistics.com", type: "shipper", phone: "+233 20 888 5678", kyc: "pending", regNum: "GH-2026-3192", submitted: "5h ago", docs: 4 },
  { id: "U-403", name: "Nana Express", email: "nana@nanaexpress.gh", type: "courier", phone: "+233 27 333 9876", kyc: "pending", regNum: "", submitted: "8h ago", docs: 1 },
  { id: "U-404", name: "GoldCoast Freight", email: "ops@goldcoast.gh", type: "shipper", phone: "+233 50 111 4567", kyc: "pending", regNum: "GH-2025-8871", submitted: "1d ago", docs: 5 },
  { id: "U-405", name: "Yaw Mensah", email: "yaw.m@gmail.com", type: "courier", phone: "+233 24 700 1111", kyc: "rejected", regNum: "", submitted: "2d ago", docs: 0 },
  { id: "U-406", name: "Eastern Star Haulage", email: "hello@easternstar.gh", type: "courier", phone: "+233 55 222 3333", kyc: "pending", regNum: "GH-2026-0512", submitted: "3h ago", docs: 4 },
];

/* ═══════════════════════════════════════════════════════════════
   MOCK DATA — FRAUD ALERTS
   ═══════════════════════════════════════════════════════════════ */

const FRAUD_ALERTS = [
  { id: "FA-101", user: "QuickMove GH", category: "payment_abuse", severity: "critical", score: 89, title: "Rapid deposit-withdraw cycles detected", status: "open", time: "25m ago" },
  { id: "FA-102", user: "PhantomShip Ltd", category: "fake_company", severity: "critical", score: 82, title: "12 listings, 0 completed trips, KYC rejected", status: "open", time: "1h ago" },
  { id: "FA-103", user: "BidBot247", category: "suspicious_bidding", severity: "high", score: 71, title: "48 bids in 24h with 2% acceptance rate", status: "investigating", time: "3h ago" },
  { id: "FA-104", user: "CheapFreight", category: "unusual_pricing", severity: "high", score: 64, title: "Bids consistently 70% below market average", status: "investigating", time: "5h ago" },
  { id: "FA-105", user: "CancelKing", category: "repeated_cancellation", severity: "medium", score: 48, title: "8 cancellations in 7 days after bid acceptance", status: "open", time: "6h ago" },
  { id: "FA-106", user: "SplitPay User", category: "payment_abuse", severity: "high", score: 67, title: "Transaction splitting — 6 deposits summing to GHS 5,000", status: "open", time: "8h ago" },
  { id: "FA-107", user: "NoVerify Courier", category: "fake_company", severity: "medium", score: 42, title: "No KYC, no email verification after 30 days", status: "escalated", time: "1d ago" },
];

/* ═══════════════════════════════════════════════════════════════
   MOCK DATA — REGIONAL HEAT MAP
   ═══════════════════════════════════════════════════════════════ */

const REGIONS = [
  { name: "Greater Accra", loads: 412, revenue: 680000, couriers: 820, heat: 100 },
  { name: "Ashanti", loads: 287, revenue: 412000, couriers: 540, heat: 70 },
  { name: "Western", loads: 142, revenue: 198000, couriers: 280, heat: 35 },
  { name: "Northern", loads: 98, revenue: 142000, couriers: 190, heat: 24 },
  { name: "Central", loads: 87, revenue: 120000, couriers: 165, heat: 21 },
  { name: "Eastern", loads: 68, revenue: 96000, couriers: 130, heat: 17 },
  { name: "Volta", loads: 52, revenue: 72000, couriers: 95, heat: 13 },
  { name: "Bono", loads: 34, revenue: 48000, couriers: 64, heat: 8 },
  { name: "Upper East", loads: 28, revenue: 36000, couriers: 52, heat: 7 },
  { name: "Upper West", loads: 22, revenue: 28000, couriers: 38, heat: 5 },
  { name: "Savannah", loads: 17, revenue: 22000, couriers: 28, heat: 4 },
];

/* ═══════════════════════════════════════════════════════════════
   MOCK DATA — COMMISSION TRACKING
   ═══════════════════════════════════════════════════════════════ */

const COMMISSION_DATA = [
  { id: "C-001", trip: "L-3001", shipper: "GoldCoast Freight", courier: "Kwame Transport", amount: 2400, commission: 120, rate: 5.0, status: "collected", date: "Feb 12" },
  { id: "C-002", trip: "L-3002", shipper: "Ama Logistics", courier: "Eastern Star", amount: 3800, commission: 190, rate: 5.0, status: "collected", date: "Feb 11" },
  { id: "C-003", trip: "L-3003", shipper: "TechShip GH", courier: "Nana Express", amount: 1650, commission: 82.50, rate: 5.0, status: "pending", date: "Feb 11" },
  { id: "C-004", trip: "L-3004", shipper: "FarmFresh Co", courier: "QuickHaul", amount: 5200, commission: 260, rate: 5.0, status: "collected", date: "Feb 10" },
  { id: "C-005", trip: "L-3005", shipper: "MineCo Ghana", courier: "HeavyDuty Ltd", amount: 8400, commission: 420, rate: 5.0, status: "in_escrow", date: "Feb 10" },
  { id: "C-006", trip: "L-3006", shipper: "MediSupply", courier: "ColdChain GH", amount: 4100, commission: 205, rate: 5.0, status: "collected", date: "Feb 9" },
  { id: "C-007", trip: "L-3007", shipper: "TextileHub", courier: "SpeedFreight", amount: 1900, commission: 95, rate: 5.0, status: "disputed", date: "Feb 8" },
];

/* ═══════════════════════════════════════════════════════════════
   MOCK DATA — COMPLIANCE
   ═══════════════════════════════════════════════════════════════ */

const COMPLIANCE_ITEMS = [
  { id: "CR-01", user: "HeavyDuty Ltd", type: "Vehicle registration expired", severity: "high", status: "open", due: "Feb 15", category: "vehicle" },
  { id: "CR-02", user: "QuickHaul", type: "Insurance certificate missing", severity: "critical", status: "open", due: "Feb 13", category: "insurance" },
  { id: "CR-03", user: "GoldCoast Freight", type: "Business license renewal required", severity: "medium", status: "in_review", due: "Feb 28", category: "license" },
  { id: "CR-04", user: "ColdChain GH", type: "Temperature logger calibration overdue", severity: "medium", status: "in_review", due: "Mar 1", category: "equipment" },
  { id: "CR-05", user: "Eastern Star", type: "Driver license expiry — 2 drivers", severity: "high", status: "open", due: "Feb 18", category: "driver" },
  { id: "CR-06", user: "Nana Express", type: "AML transaction report pending submission", severity: "critical", status: "open", due: "Feb 14", category: "aml" },
  { id: "CR-07", user: "Kofi Transport", type: "Annual safety inspection needed", severity: "medium", status: "scheduled", due: "Mar 5", category: "safety" },
  { id: "CR-08", user: "SpeedFreight", type: "Data protection registration lapsed", severity: "low", status: "open", due: "Mar 15", category: "data" },
];

/* ═══════════════════════════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════════════════════════ */

function MiniBar({ data, color, height = 28 }: { data: number[]; color: string; height?: number }) {
  const max = Math.max(...data);
  return (
    <div className="flex items-end gap-[3px]" style={{ height }}>
      {data.map((v, i) => (
        <div key={i} className={`flex-1 rounded-t ${color}`} style={{ height: `${(v / max) * 100}%`, minHeight: 2 }} />
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   ADMIN DASHBOARD COMPONENT
   ═══════════════════════════════════════════════════════════════ */

export default function AdminDashboard() {
  const { activeSection: section, setActiveSection: setSection } = useAdmin();
  const maxRev = Math.max(...REVENUE_MONTHLY.map((r) => r.revenue));
  const maxLoad = Math.max(...LOAD_VOLUME.map((l) => l.count));

  const severityBadge = (s: string) => {
    if (s === "critical") return "badge-red";
    if (s === "high") return "bg-orange-50 text-orange-700 ring-1 ring-orange-600/20 badge";
    if (s === "medium") return "badge-yellow";
    return "badge-gray";
  };

  const alertStatusBadge = (s: string) => {
    if (s === "open") return "badge-red";
    if (s === "investigating") return "badge-yellow";
    if (s === "escalated") return "bg-purple-50 text-purple-700 ring-1 ring-purple-600/20 badge";
    return "badge-green";
  };

  return (
    <AdminLayout>
      <div>

          {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              SECTION: OVERVIEW
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
          {section === "overview" && (
            <div className="space-y-6">
              {/* KPI Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
                {KPI.map((k) => (
                  <div key={k.label} className="card">
                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">{k.label}</p>
                    <p className="mt-1.5 text-xl font-bold text-gray-900 dark:text-white">{k.value}</p>
                    <div className="flex items-center gap-1 mt-1">
                      <span className={`text-xs font-medium ${k.up && k.label !== "Fraud Alerts" ? "text-emerald-600" : "text-red-600"}`}>{k.delta}</span>
                      <span className="text-[10px] text-gray-400">{k.sub}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="grid lg:grid-cols-2 gap-6">
                {/* Revenue chart */}
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">Monthly Revenue</h3>
                  <div className="flex items-end gap-3 h-40">
                    {REVENUE_MONTHLY.map((r) => (
                      <div key={r.month} className="flex-1 flex flex-col items-center gap-1">
                        <span className="text-[10px] text-gray-500">{(r.revenue / 1000).toFixed(0)}k</span>
                        <div className="w-full rounded-t bg-brand-500" style={{ height: `${(r.revenue / maxRev) * 100}%` }} />
                        <span className="text-[10px] text-gray-400">{r.month}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Load volume chart */}
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">Load Volume</h3>
                  <div className="flex items-end gap-3 h-40">
                    {LOAD_VOLUME.map((l) => (
                      <div key={l.month} className="flex-1 flex flex-col items-center gap-1">
                        <span className="text-[10px] text-gray-500">{l.count}</span>
                        <div className="w-full rounded-t bg-blue-500" style={{ height: `${(l.count / maxLoad) * 100}%` }} />
                        <span className="text-[10px] text-gray-400">{l.month}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Quick Lists */}
              <div className="grid lg:grid-cols-2 gap-6">
                {/* Recent fraud alerts */}
                <div className="card">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-gray-700">Recent Fraud Alerts</h3>
                    <button onClick={() => setSection("fraud")} className="text-xs text-brand-600 hover:underline">View all</button>
                  </div>
                  <div className="space-y-2.5">
                    {FRAUD_ALERTS.slice(0, 4).map((a) => (
                      <div key={a.id} className="flex items-start gap-3">
                        <div className={`mt-0.5 h-2 w-2 rounded-full shrink-0 ${a.severity === "critical" ? "bg-red-500" : a.severity === "high" ? "bg-orange-500" : "bg-amber-400"}`} />
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-gray-900 truncate">{a.title}</p>
                          <p className="text-[10px] text-gray-500">{a.user} &middot; {a.time}</p>
                        </div>
                        <span className={severityBadge(a.severity)}>{a.severity}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Pending approvals */}
                <div className="card">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-gray-700">Pending User Approvals</h3>
                    <button onClick={() => setSection("users")} className="text-xs text-brand-600 hover:underline">View all</button>
                  </div>
                  <div className="space-y-2.5">
                    {PENDING_USERS.slice(0, 4).map((u) => (
                      <div key={u.id} className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-semibold text-gray-600">{u.name.split(" ").map((w) => w[0]).join("").slice(0, 2)}</div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-gray-900 truncate">{u.name}</p>
                          <p className="text-[10px] text-gray-500">{u.type} &middot; {u.submitted}</p>
                        </div>
                        <span className={u.docs >= 3 ? "badge-green" : "badge-yellow"}>{u.docs} docs</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              SECTION: USER APPROVALS
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
          {section === "users" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">{PENDING_USERS.length} users pending review</p>
                <div className="flex gap-2">
                  <select className="input py-1.5 text-xs w-32"><option>All Types</option><option>Shipper</option><option>Courier</option></select>
                  <select className="input py-1.5 text-xs w-32"><option>All Status</option><option>Pending</option><option>Rejected</option></select>
                </div>
              </div>
              {PENDING_USERS.map((u) => (
                <div key={u.id} className="card-hover">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className="h-11 w-11 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold text-gray-600 shrink-0">{u.name.split(" ").map((w) => w[0]).join("").slice(0, 2)}</div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-semibold text-gray-900">{u.name}</p>
                          <span className={u.type === "courier" ? "badge-blue" : "badge-green"}>{u.type}</span>
                          <span className={u.kyc === "rejected" ? "badge-red" : "badge-yellow"}>KYC: {u.kyc}</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">{u.email} &middot; {u.phone}</p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {u.regNum ? `Reg: ${u.regNum}` : "No registration number"} &middot; {u.docs} document{u.docs !== 1 ? "s" : ""} &middot; Submitted {u.submitted}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button className="btn-primary text-xs px-3 py-2">Approve</button>
                      <button className="btn-secondary text-xs px-3 py-2">Reject</button>
                      <button className="btn-secondary text-xs px-3 py-2">View Docs</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              SECTION: FRAUD ALERTS
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
          {section === "fraud" && (
            <div className="space-y-4">
              {/* Fraud summary cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: "Open Alerts", value: "4", color: "text-red-600" },
                  { label: "Investigating", value: "2", color: "text-amber-600" },
                  { label: "Escalated", value: "1", color: "text-purple-600" },
                  { label: "Avg Risk Score", value: "66.1", color: "text-gray-900" },
                ].map((s) => (
                  <div key={s.label} className="card">
                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">{s.label}</p>
                    <p className={`mt-1 text-xl font-bold ${s.color}`}>{s.value}</p>
                  </div>
                ))}
              </div>

              {/* Alerts list */}
              {FRAUD_ALERTS.map((a) => (
                <div key={a.id} className={`card-hover border-l-4 ${a.severity === "critical" ? "border-l-red-500" : a.severity === "high" ? "border-l-orange-400" : "border-l-amber-300"}`}>
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-semibold text-gray-900">{a.title}</h3>
                        <span className={severityBadge(a.severity)}>{a.severity}</span>
                        <span className={alertStatusBadge(a.status)}>{a.status}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        <span className="font-medium text-gray-700">{a.user}</span> &middot; {a.category.replace("_", " ")} &middot; Risk score: <span className="font-semibold">{a.score}/100</span> &middot; {a.time}
                      </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button className="btn-primary text-xs px-3 py-2">Investigate</button>
                      <button className="btn-secondary text-xs px-3 py-2">Dismiss</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              SECTION: REVENUE
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
          {section === "revenue" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: "Total Revenue (6mo)", value: "GHS 1.54M", delta: "+12%" },
                  { label: "Total Commission", value: "GHS 77K", delta: "+11%" },
                  { label: "Avg Trip Value", value: "GHS 2,280", delta: "+5%" },
                  { label: "Commission Rate", value: "5.0%", delta: "Flat" },
                ].map((s) => (
                  <div key={s.label} className="card">
                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">{s.label}</p>
                    <p className="mt-1 text-xl font-bold text-gray-900">{s.value}</p>
                    <p className="text-xs text-emerald-600 mt-0.5">{s.delta}</p>
                  </div>
                ))}
              </div>

              <div className="card">
                <h3 className="text-sm font-semibold text-gray-700 mb-4">Revenue vs Commission (6 months)</h3>
                <div className="flex items-end gap-4 h-52">
                  {REVENUE_MONTHLY.map((r) => (
                    <div key={r.month} className="flex-1 flex flex-col items-center gap-1">
                      <span className="text-[10px] text-gray-500">{(r.revenue / 1000).toFixed(0)}k</span>
                      <div className="w-full flex gap-1">
                        <div className="flex-1 rounded-t bg-brand-500" style={{ height: `${(r.revenue / maxRev) * 200}px` }} />
                        <div className="flex-1 rounded-t bg-accent-400" style={{ height: `${(r.commission / maxRev) * 200}px` }} />
                      </div>
                      <span className="text-[10px] text-gray-400">{r.month}</span>
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-6 mt-4 pt-3 border-t border-gray-100">
                  <div className="flex items-center gap-2 text-xs text-gray-500"><div className="h-2.5 w-2.5 rounded bg-brand-500" /> Revenue</div>
                  <div className="flex items-center gap-2 text-xs text-gray-500"><div className="h-2.5 w-2.5 rounded bg-accent-400" /> Commission</div>
                </div>
              </div>
            </div>
          )}

          {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              SECTION: LOAD ANALYTICS
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
          {section === "loads" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
                {[
                  { label: "Total Loads", value: "6,239" },
                  { label: "Active Now", value: "134" },
                  { label: "Avg Bids/Load", value: "4.2" },
                  { label: "Completion Rate", value: "91.3%" },
                  { label: "Avg Distance", value: "218 km" },
                ].map((s) => (
                  <div key={s.label} className="card">
                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">{s.label}</p>
                    <p className="mt-1 text-xl font-bold text-gray-900">{s.value}</p>
                  </div>
                ))}
              </div>

              <div className="grid lg:grid-cols-2 gap-6">
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">Loads by Month</h3>
                  <div className="flex items-end gap-3 h-44">
                    {LOAD_VOLUME.map((l) => (
                      <div key={l.month} className="flex-1 flex flex-col items-center gap-1">
                        <span className="text-[10px] text-gray-500">{l.count}</span>
                        <div className="w-full rounded-t bg-blue-500" style={{ height: `${(l.count / maxLoad) * 100}%` }} />
                        <span className="text-[10px] text-gray-400">{l.month}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">Loads by Cargo Type</h3>
                  <div className="space-y-2.5">
                    {[
                      { type: "General", pct: 32 },
                      { type: "Electronics", pct: 18 },
                      { type: "Perishables", pct: 14 },
                      { type: "Construction", pct: 12 },
                      { type: "Textiles", pct: 9 },
                      { type: "Medical", pct: 7 },
                      { type: "Furniture", pct: 5 },
                      { type: "Other", pct: 3 },
                    ].map((c) => (
                      <div key={c.type} className="flex items-center gap-3">
                        <span className="text-xs text-gray-600 w-24 shrink-0">{c.type}</span>
                        <div className="flex-1 h-3 rounded-full bg-gray-100 overflow-hidden">
                          <div className="h-full rounded-full bg-brand-500" style={{ width: `${c.pct}%` }} />
                        </div>
                        <span className="text-xs font-medium text-gray-700 w-10 text-right">{c.pct}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="card">
                <h3 className="text-sm font-semibold text-gray-700 mb-4">Top Routes</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 uppercase">Route</th>
                        <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 uppercase">Loads</th>
                        <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 uppercase">Avg Price</th>
                        <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 uppercase">Revenue</th>
                        <th className="text-center py-2 px-3 text-xs font-medium text-gray-500 uppercase">Trend</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { route: "Accra → Kumasi", loads: 412, avg: 1850, rev: 762200, trend: [3, 5, 4, 7, 6, 8] },
                        { route: "Tema → Takoradi", loads: 287, avg: 2100, rev: 602700, trend: [2, 3, 5, 4, 6, 7] },
                        { route: "Accra → Tamale", loads: 198, avg: 3400, rev: 673200, trend: [4, 3, 5, 6, 7, 9] },
                        { route: "Kumasi → Tamale", loads: 142, avg: 2800, rev: 397600, trend: [2, 4, 3, 5, 4, 6] },
                        { route: "Tema → Kumasi", loads: 134, avg: 2050, rev: 274700, trend: [3, 4, 4, 5, 5, 6] },
                      ].map((r) => (
                        <tr key={r.route} className="border-b border-gray-50 hover:bg-gray-50/50">
                          <td className="py-3 px-3 font-medium text-gray-900">{r.route}</td>
                          <td className="py-3 px-3 text-right text-gray-700">{r.loads}</td>
                          <td className="py-3 px-3 text-right text-gray-700">GHS {r.avg.toLocaleString()}</td>
                          <td className="py-3 px-3 text-right font-medium text-gray-900">GHS {r.rev.toLocaleString()}</td>
                          <td className="py-3 px-3"><MiniBar data={r.trend} color="bg-brand-400" /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              SECTION: REGIONAL HEAT MAP
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
          {section === "regions" && (
            <div className="space-y-6">
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Heat map visual */}
                <div className="lg:col-span-2 card">
                  <h3 className="text-sm font-semibold text-gray-700 mb-4">Ghana Regional Load Density</h3>
                  <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                    {REGIONS.map((r) => {
                      const intensity = Math.round((r.heat / 100) * 255);
                      const bg = r.heat >= 60 ? `rgb(${255 - intensity / 2}, ${Math.max(40, intensity)}, ${Math.max(40, intensity / 2)})` : r.heat >= 20 ? `rgb(255, ${200 - intensity}, ${80})` : `rgb(${220 + intensity / 8}, ${230 + intensity / 10}, ${220 + intensity / 8})`;
                      return (
                        <div
                          key={r.name}
                          className="rounded-xl p-4 text-center transition hover:scale-105 cursor-pointer"
                          style={{ backgroundColor: `rgba(22, 163, 74, ${r.heat / 100 * 0.7 + 0.05})` }}
                        >
                          <p className={`text-xs font-bold ${r.heat >= 50 ? "text-white" : "text-gray-700"}`}>{r.name.replace("Greater ", "Gr. ")}</p>
                          <p className={`text-lg font-black mt-1 ${r.heat >= 50 ? "text-white" : "text-gray-900"}`}>{r.loads}</p>
                          <p className={`text-[10px] ${r.heat >= 50 ? "text-white/80" : "text-gray-500"}`}>loads</p>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex items-center justify-center gap-2 mt-4 pt-3 border-t border-gray-100">
                    <span className="text-[10px] text-gray-400">Low</span>
                    <div className="flex h-2.5 rounded-full overflow-hidden w-40">
                      <div className="flex-1 bg-brand-100" />
                      <div className="flex-1 bg-brand-300" />
                      <div className="flex-1 bg-brand-500" />
                      <div className="flex-1 bg-brand-700" />
                      <div className="flex-1 bg-brand-900" />
                    </div>
                    <span className="text-[10px] text-gray-400">High</span>
                  </div>
                </div>

                {/* Region stats table */}
                <div className="card">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">By Region</h3>
                  <div className="space-y-2">
                    {REGIONS.map((r) => (
                      <div key={r.name} className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: `rgba(22, 163, 74, ${r.heat / 100 * 0.8 + 0.2})` }} />
                        <span className="text-xs text-gray-700 flex-1 truncate">{r.name}</span>
                        <span className="text-xs font-semibold text-gray-900 w-10 text-right">{r.loads}</span>
                        <span className="text-[10px] text-gray-400 w-16 text-right">GHS {(r.revenue / 1000).toFixed(0)}k</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 pt-3 border-t border-gray-100 flex justify-between text-xs">
                    <span className="text-gray-500">Total</span>
                    <span className="font-semibold text-gray-700">{REGIONS.reduce((a, r) => a + r.loads, 0).toLocaleString()} loads</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              SECTION: COMMISSION TRACKING
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
          {section === "commission" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: "Collected (Feb)", value: "GHS 14,200", color: "text-emerald-600" },
                  { label: "Pending", value: "GHS 82.50", color: "text-amber-600" },
                  { label: "In Escrow", value: "GHS 420", color: "text-blue-600" },
                  { label: "Disputed", value: "GHS 95", color: "text-red-600" },
                ].map((s) => (
                  <div key={s.label} className="card">
                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">{s.label}</p>
                    <p className={`mt-1 text-xl font-bold ${s.color}`}>{s.value}</p>
                  </div>
                ))}
              </div>

              <div className="card overflow-hidden">
                <h3 className="text-sm font-semibold text-gray-700 mb-4">Commission Ledger</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 uppercase">ID</th>
                        <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 uppercase">Trip</th>
                        <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 uppercase">Shipper</th>
                        <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 uppercase">Courier</th>
                        <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 uppercase">Trip Value</th>
                        <th className="text-right py-2 px-3 text-xs font-medium text-gray-500 uppercase">Commission</th>
                        <th className="text-center py-2 px-3 text-xs font-medium text-gray-500 uppercase">Rate</th>
                        <th className="text-center py-2 px-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="text-left py-2 px-3 text-xs font-medium text-gray-500 uppercase">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {COMMISSION_DATA.map((c) => (
                        <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                          <td className="py-2.5 px-3 text-gray-500 font-mono text-xs">{c.id}</td>
                          <td className="py-2.5 px-3 text-gray-700">{c.trip}</td>
                          <td className="py-2.5 px-3 text-gray-700">{c.shipper}</td>
                          <td className="py-2.5 px-3 text-gray-700">{c.courier}</td>
                          <td className="py-2.5 px-3 text-right font-medium text-gray-900">GHS {c.amount.toLocaleString()}</td>
                          <td className="py-2.5 px-3 text-right font-semibold text-brand-700">GHS {c.commission.toLocaleString()}</td>
                          <td className="py-2.5 px-3 text-center text-gray-500">{c.rate}%</td>
                          <td className="py-2.5 px-3 text-center">
                            <span className={c.status === "collected" ? "badge-green" : c.status === "pending" ? "badge-yellow" : c.status === "in_escrow" ? "badge-blue" : "badge-red"}>{c.status.replace("_", " ")}</span>
                          </td>
                          <td className="py-2.5 px-3 text-gray-500">{c.date}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
                  <p className="text-xs text-gray-500">Total commission: <span className="font-semibold text-gray-700">GHS {COMMISSION_DATA.reduce((a, c) => a + c.commission, 0).toLocaleString()}</span></p>
                  <button className="btn-secondary text-xs py-1.5 px-3">Export CSV</button>
                </div>
              </div>
            </div>
          )}

          {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              SECTION: COMPLIANCE
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
          {section === "compliance" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: "Open Issues", value: "5", color: "text-red-600" },
                  { label: "In Review", value: "2", color: "text-amber-600" },
                  { label: "Scheduled", value: "1", color: "text-blue-600" },
                  { label: "Overdue (<3 days)", value: "2", color: "text-red-700" },
                ].map((s) => (
                  <div key={s.label} className="card">
                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">{s.label}</p>
                    <p className={`mt-1 text-xl font-bold ${s.color}`}>{s.value}</p>
                  </div>
                ))}
              </div>

              {COMPLIANCE_ITEMS.map((c) => (
                <div key={c.id} className={`card-hover border-l-4 ${c.severity === "critical" ? "border-l-red-500" : c.severity === "high" ? "border-l-orange-400" : c.severity === "medium" ? "border-l-amber-300" : "border-l-gray-300"}`}>
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-semibold text-gray-900">{c.type}</h3>
                        <span className={severityBadge(c.severity)}>{c.severity}</span>
                        <span className={c.status === "open" ? "badge-red" : c.status === "in_review" ? "badge-yellow" : "badge-blue"}>{c.status.replace("_", " ")}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        <span className="font-medium text-gray-700">{c.user}</span> &middot; Category: {c.category} &middot; Due: <span className="font-medium">{c.due}</span>
                      </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button className="btn-primary text-xs px-3 py-2">Review</button>
                      <button className="btn-secondary text-xs px-3 py-2">Send Reminder</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

      </div>
    </AdminLayout>
  );
}
