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

/* ── Mock document data per user ────────────────────────────── */
const USER_DOCS: Record<string, { name: string; type: string; size: string; uploaded: string }[]> = {
  "U-401": [
    { name: "Business Registration Certificate", type: "PDF", size: "1.2 MB", uploaded: "2h ago" },
    { name: "Vehicle Insurance - Truck #1", type: "PDF", size: "890 KB", uploaded: "2h ago" },
    { name: "Driver License - Kofi Mensah", type: "Image", size: "2.1 MB", uploaded: "2h ago" },
  ],
  "U-402": [
    { name: "Company Registration (GRA)", type: "PDF", size: "1.8 MB", uploaded: "5h ago" },
    { name: "Tax Clearance Certificate", type: "PDF", size: "540 KB", uploaded: "5h ago" },
    { name: "Warehouse Lease Agreement", type: "PDF", size: "3.2 MB", uploaded: "5h ago" },
    { name: "ID Card - Ama Osei", type: "Image", size: "1.4 MB", uploaded: "5h ago" },
  ],
  "U-403": [
    { name: "Ghana Card - Nana Kweku", type: "Image", size: "1.1 MB", uploaded: "8h ago" },
  ],
  "U-404": [
    { name: "Certificate of Incorporation", type: "PDF", size: "2.0 MB", uploaded: "1d ago" },
    { name: "Directors Resolution", type: "PDF", size: "780 KB", uploaded: "1d ago" },
    { name: "Fleet Registration (DVLA)", type: "PDF", size: "1.5 MB", uploaded: "1d ago" },
    { name: "Insurance Bundle - 3 Vehicles", type: "PDF", size: "4.1 MB", uploaded: "1d ago" },
    { name: "Tax Identification Number", type: "PDF", size: "320 KB", uploaded: "1d ago" },
  ],
  "U-405": [],
  "U-406": [
    { name: "Business Registration", type: "PDF", size: "1.3 MB", uploaded: "3h ago" },
    { name: "Vehicle Registration - Truck A", type: "PDF", size: "920 KB", uploaded: "3h ago" },
    { name: "Vehicle Registration - Truck B", type: "PDF", size: "910 KB", uploaded: "3h ago" },
    { name: "Driver Licenses (2 drivers)", type: "PDF", size: "2.8 MB", uploaded: "3h ago" },
  ],
};

export default function AdminDashboard() {
  const { activeSection: section, setActiveSection: setSection } = useAdmin();
  const maxRev = Math.max(...REVENUE_MONTHLY.map((r) => r.revenue));
  const maxLoad = Math.max(...LOAD_VOLUME.map((l) => l.count));

  /* ── User management state ─────────────────────────────── */
  const [users, setUsers] = useState(PENDING_USERS.map((u) => ({ ...u })));
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);
  const [viewDocsUser, setViewDocsUser] = useState<string | null>(null);
  const [rejectConfirm, setRejectConfirm] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  /* ── User filter state ──────────────────────────────────── */
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");

  /* Sync sidebar submenu with filter status */
  const effectiveStatus = section === "users-approved" ? "approved" : section === "users-rejected" ? "rejected" : filterStatus;
  const isUsersSection = section === "users" || section === "users-approved" || section === "users-rejected";

  const filteredUsers = users.filter((u) => {
    if (filterType !== "all" && u.type !== filterType) return false;
    if (effectiveStatus !== "all" && u.kyc !== effectiveStatus) return false;
    return true;
  });

  /* ── Fraud management state ────────────────────────────── */
  const [fraudAlerts, setFraudAlerts] = useState(FRAUD_ALERTS.map((a) => ({ ...a })));

  /* ── Compliance state ──────────────────────────────────── */
  const [complianceItems, setComplianceItems] = useState(COMPLIANCE_ITEMS.map((c) => ({ ...c })));
  const [reviewItem, setReviewItem] = useState<string | null>(null);
  const [reviewNote, setReviewNote] = useState("");

  function showToast(message: string, type: "success" | "error" | "info" = "success") {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  }

  function handleApprove(id: string) {
    setUsers((prev) => prev.map((u) => u.id === id ? { ...u, kyc: "approved" } : u));
    const user = users.find((u) => u.id === id);
    showToast(`${user?.name} has been approved successfully.`, "success");
  }

  function handleReject(id: string) {
    setRejectConfirm(id);
    setRejectReason("");
  }

  function confirmReject() {
    if (!rejectConfirm) return;
    setUsers((prev) => prev.map((u) => u.id === rejectConfirm ? { ...u, kyc: "rejected" } : u));
    const user = users.find((u) => u.id === rejectConfirm);
    showToast(`${user?.name} has been rejected.`, "error");
    setRejectConfirm(null);
    setRejectReason("");
  }

  function handleInvestigate(id: string) {
    setFraudAlerts((prev) => prev.map((a) => a.id === id ? { ...a, status: "investigating" } : a));
    const alert = fraudAlerts.find((a) => a.id === id);
    showToast(`Investigating: ${alert?.user}`, "info");
  }

  function handleDismiss(id: string) {
    setFraudAlerts((prev) => prev.filter((a) => a.id !== id));
    showToast("Alert dismissed.", "info");
  }

  function handleComplianceReview(id: string) {
    setReviewItem(id);
    setReviewNote("");
  }

  function confirmComplianceReview() {
    if (!reviewItem) return;
    setComplianceItems((prev) => prev.map((c) => c.id === reviewItem ? { ...c, status: "in_review" } : c));
    const item = complianceItems.find((c) => c.id === reviewItem);
    showToast(`${item?.type} for ${item?.user} is now under review.`, "info");
    setReviewItem(null);
    setReviewNote("");
  }

  function handleComplianceResolve(id: string) {
    setComplianceItems((prev) => prev.map((c) => c.id === id ? { ...c, status: "resolved" } : c));
    const item = complianceItems.find((c) => c.id === id);
    showToast(`${item?.type} for ${item?.user} has been resolved.`, "success");
  }

  function handleSendReminder(id: string) {
    const item = complianceItems.find((c) => c.id === id);
    showToast(`Reminder sent to ${item?.user} for: ${item?.type}`, "success");
  }

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

  const kycBadge = (s: string) => {
    if (s === "approved") return "badge-green";
    if (s === "rejected") return "badge-red";
    return "badge-yellow";
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
          {isUsersSection && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {filteredUsers.length} user{filteredUsers.length !== 1 ? "s" : ""} shown &middot; {users.filter((u) => u.kyc === "pending").length} pending
                </p>
                <div className="flex gap-2">
                  <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="input py-1.5 text-xs w-32">
                    <option value="all">All Types</option>
                    <option value="shipper">Shipper</option>
                    <option value="courier">Courier</option>
                  </select>
                  <select
                    value={effectiveStatus}
                    onChange={(e) => { setFilterStatus(e.target.value); if (section !== "users") setSection("users"); }}
                    className="input py-1.5 text-xs w-32"
                  >
                    <option value="all">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
              </div>
              {filteredUsers.length === 0 ? (
                <div className="card text-center py-10">
                  <svg className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" /></svg>
                  <p className="text-sm font-semibold text-gray-500 dark:text-gray-400">No users match filters</p>
                  <p className="text-xs text-gray-400 mt-1">Try changing the type or status filter.</p>
                </div>
              ) : null}
              {filteredUsers.map((u) => (
                <div key={u.id} className={`card-hover transition-all ${u.kyc === "approved" ? "border-l-4 border-l-emerald-500" : u.kyc === "rejected" ? "border-l-4 border-l-red-400 opacity-75" : ""}`}>
                  <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <div className={`h-11 w-11 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${u.kyc === "approved" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" : u.kyc === "rejected" ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400" : "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300"}`}>
                        {u.kyc === "approved" ? (
                          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
                        ) : u.kyc === "rejected" ? (
                          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                        ) : (
                          u.name.split(" ").map((w) => w[0]).join("").slice(0, 2)
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-semibold text-gray-900 dark:text-white">{u.name}</p>
                          <span className={u.type === "courier" ? "badge-blue" : "badge-green"}>{u.type}</span>
                          <span className={kycBadge(u.kyc)}>KYC: {u.kyc}</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">{u.email} &middot; {u.phone}</p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {u.regNum ? `Reg: ${u.regNum}` : "No registration number"} &middot; {u.docs} document{u.docs !== 1 ? "s" : ""} &middot; Submitted {u.submitted}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      {u.kyc === "pending" ? (
                        <>
                          <button onClick={() => handleApprove(u.id)} className="btn-primary text-xs px-3 py-2">Approve</button>
                          <button onClick={() => handleReject(u.id)} className="btn-secondary text-xs px-3 py-2 hover:!bg-red-50 hover:!text-red-600 hover:!ring-red-200 dark:hover:!bg-red-900/20 dark:hover:!text-red-400">Reject</button>
                        </>
                      ) : u.kyc === "approved" ? (
                        <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
                          Approved
                        </span>
                      ) : (
                        <span className="text-xs font-semibold text-red-500 dark:text-red-400 flex items-center gap-1">
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                          Rejected
                        </span>
                      )}
                      <button onClick={() => setViewDocsUser(u.id)} className="btn-secondary text-xs px-3 py-2">View Docs</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── View Docs Modal ─────────────────────────── */}
          {viewDocsUser && (
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4" onClick={() => setViewDocsUser(null)}>
              <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
              <div className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-lg max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
                  <div>
                    <h3 className="text-base font-bold text-gray-900 dark:text-white">
                      {users.find((u) => u.id === viewDocsUser)?.name}
                    </h3>
                    <p className="text-xs text-gray-500 mt-0.5">Submitted Documents</p>
                  </div>
                  <button onClick={() => setViewDocsUser(null)} className="h-8 w-8 rounded-lg flex items-center justify-center text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-700 dark:hover:text-gray-200 transition">
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                  </button>
                </div>
                <div className="px-6 py-4 overflow-y-auto max-h-[60vh]">
                  {(USER_DOCS[viewDocsUser] || []).length === 0 ? (
                    <div className="text-center py-8">
                      <svg className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
                      <p className="text-sm text-gray-500 dark:text-gray-400">No documents submitted</p>
                      <p className="text-xs text-gray-400 mt-1">This user has not uploaded any KYC documents yet.</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {(USER_DOCS[viewDocsUser] || []).map((doc, i) => (
                        <div key={i} className="flex items-center gap-3 rounded-lg border border-gray-100 dark:border-gray-800 p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition">
                          <div className={`h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0 ${doc.type === "PDF" ? "bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400" : "bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400"}`}>
                            {doc.type === "PDF" ? (
                              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" /></svg>
                            ) : (
                              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" /></svg>
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{doc.name}</p>
                            <p className="text-[11px] text-gray-400">{doc.type} &middot; {doc.size} &middot; Uploaded {doc.uploaded}</p>
                          </div>
                          <button className="text-xs font-medium text-brand-600 dark:text-brand-400 hover:underline flex-shrink-0">Download</button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="px-6 py-3 border-t border-gray-100 dark:border-gray-800 flex justify-end">
                  <button onClick={() => setViewDocsUser(null)} className="btn-secondary text-sm">Close</button>
                </div>
              </div>
            </div>
          )}

          {/* ── Reject Confirmation Modal ───────────────── */}
          {rejectConfirm && (
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4" onClick={() => setRejectConfirm(null)}>
              <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
              <div className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md overflow-hidden" onClick={(e) => e.stopPropagation()}>
                <div className="px-6 py-5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="h-10 w-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center flex-shrink-0">
                      <svg className="h-5 w-5 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg>
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-white">Reject User</h3>
                      <p className="text-xs text-gray-500">
                        Reject <span className="font-semibold text-gray-700 dark:text-gray-300">{users.find((u) => u.id === rejectConfirm)?.name}</span>?
                      </p>
                    </div>
                  </div>
                  <label className="label">Reason for rejection</label>
                  <textarea
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    className="input h-24 resize-none"
                    placeholder="e.g. Missing vehicle registration documents..."
                  />
                </div>
                <div className="px-6 py-3 border-t border-gray-100 dark:border-gray-800 flex justify-end gap-2">
                  <button onClick={() => setRejectConfirm(null)} className="btn-secondary text-sm">Cancel</button>
                  <button onClick={confirmReject} className="inline-flex items-center justify-center rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-red-700">
                    Confirm Reject
                  </button>
                </div>
              </div>
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
              {fraudAlerts.length === 0 ? (
                <div className="card text-center py-10">
                  <svg className="h-12 w-12 text-emerald-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">All clear!</p>
                  <p className="text-xs text-gray-400 mt-1">No active fraud alerts.</p>
                </div>
              ) : (
                fraudAlerts.map((a) => (
                  <div key={a.id} className={`card-hover border-l-4 ${a.severity === "critical" ? "border-l-red-500" : a.severity === "high" ? "border-l-orange-400" : "border-l-amber-300"}`}>
                    <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{a.title}</h3>
                          <span className={severityBadge(a.severity)}>{a.severity}</span>
                          <span className={alertStatusBadge(a.status)}>{a.status}</span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          <span className="font-medium text-gray-700 dark:text-gray-300">{a.user}</span> &middot; {a.category.replace("_", " ")} &middot; Risk score: <span className="font-semibold">{a.score}/100</span> &middot; {a.time}
                        </p>
                      </div>
                      <div className="flex gap-2 shrink-0">
                        {a.status !== "investigating" ? (
                          <button onClick={() => handleInvestigate(a.id)} className="btn-primary text-xs px-3 py-2">Investigate</button>
                        ) : (
                          <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 flex items-center gap-1">
                            <svg className="h-4 w-4 animate-pulse" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                            Investigating
                          </span>
                        )}
                        <button onClick={() => handleDismiss(a.id)} className="btn-secondary text-xs px-3 py-2 hover:!bg-red-50 hover:!text-red-600 dark:hover:!bg-red-900/20 dark:hover:!text-red-400">Dismiss</button>
                      </div>
                    </div>
                  </div>
                ))
              )}
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
                  { label: "Open Issues", value: String(complianceItems.filter((c) => c.status === "open").length), color: "text-red-600" },
                  { label: "In Review", value: String(complianceItems.filter((c) => c.status === "in_review").length), color: "text-amber-600" },
                  { label: "Scheduled", value: String(complianceItems.filter((c) => c.status === "scheduled").length), color: "text-blue-600" },
                  { label: "Resolved", value: String(complianceItems.filter((c) => c.status === "resolved").length), color: "text-emerald-600" },
                ].map((s) => (
                  <div key={s.label} className="card">
                    <p className="text-[11px] font-medium text-gray-500 uppercase tracking-wider">{s.label}</p>
                    <p className={`mt-1 text-xl font-bold ${s.color}`}>{s.value}</p>
                  </div>
                ))}
              </div>

              {complianceItems.filter((c) => c.status !== "resolved").length === 0 ? (
                <div className="card text-center py-10">
                  <svg className="h-12 w-12 text-emerald-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                  <p className="text-sm font-semibold text-gray-700 dark:text-gray-300">All compliance issues resolved!</p>
                </div>
              ) : null}

              {complianceItems.map((c) => (
                <div key={c.id} className={`card-hover border-l-4 transition-all ${c.status === "resolved" ? "border-l-emerald-500 opacity-60" : c.severity === "critical" ? "border-l-red-500" : c.severity === "high" ? "border-l-orange-400" : c.severity === "medium" ? "border-l-amber-300" : "border-l-gray-300"}`}>
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">{c.type}</h3>
                        <span className={severityBadge(c.severity)}>{c.severity}</span>
                        <span className={c.status === "open" ? "badge-red" : c.status === "in_review" ? "badge-yellow" : c.status === "scheduled" ? "badge-blue" : "badge-green"}>{c.status.replace("_", " ")}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        <span className="font-medium text-gray-700 dark:text-gray-300">{c.user}</span> &middot; Category: {c.category} &middot; Due: <span className="font-medium">{c.due}</span>
                      </p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      {c.status === "resolved" ? (
                        <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
                          Resolved
                        </span>
                      ) : c.status === "in_review" ? (
                        <button onClick={() => handleComplianceResolve(c.id)} className="btn-primary text-xs px-3 py-2">Mark Resolved</button>
                      ) : (
                        <button onClick={() => handleComplianceReview(c.id)} className="btn-primary text-xs px-3 py-2">Review</button>
                      )}
                      {c.status !== "resolved" && (
                        <button onClick={() => handleSendReminder(c.id)} className="btn-secondary text-xs px-3 py-2">Send Reminder</button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ── Compliance Review Modal ─────────────────── */}
          {reviewItem && (
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4" onClick={() => setReviewItem(null)}>
              <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
              <div className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full max-w-md overflow-hidden" onClick={(e) => e.stopPropagation()}>
                <div className="px-6 py-5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="h-10 w-10 rounded-full bg-brand-100 dark:bg-brand-900/30 flex items-center justify-center flex-shrink-0">
                      <svg className="h-5 w-5 text-brand-600 dark:text-brand-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" /></svg>
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-gray-900 dark:text-white">Review Compliance Issue</h3>
                      <p className="text-xs text-gray-500">{complianceItems.find((c) => c.id === reviewItem)?.type}</p>
                    </div>
                  </div>
                  <div className="rounded-lg bg-gray-50 dark:bg-gray-800 p-3 mb-4 space-y-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{complianceItems.find((c) => c.id === reviewItem)?.user}</p>
                    <p className="text-xs text-gray-500">Category: {complianceItems.find((c) => c.id === reviewItem)?.category} &middot; Due: {complianceItems.find((c) => c.id === reviewItem)?.due}</p>
                    <p className="text-xs text-gray-500">Severity: <span className="font-semibold">{complianceItems.find((c) => c.id === reviewItem)?.severity}</span></p>
                  </div>
                  <label className="label">Review notes</label>
                  <textarea
                    value={reviewNote}
                    onChange={(e) => setReviewNote(e.target.value)}
                    className="input h-24 resize-none"
                    placeholder="Add notes about this compliance review..."
                  />
                </div>
                <div className="px-6 py-3 border-t border-gray-100 dark:border-gray-800 flex justify-end gap-2">
                  <button onClick={() => setReviewItem(null)} className="btn-secondary text-sm">Cancel</button>
                  <button onClick={confirmComplianceReview} className="btn-primary text-sm">Start Review</button>
                </div>
              </div>
            </div>
          )}

      </div>

      {/* ── Toast Notification ─────────────────────── */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-[70] animate-slide-up">
          <div className={`flex items-center gap-3 rounded-xl px-5 py-3.5 shadow-2xl border ${
            toast.type === "success" ? "bg-emerald-600 border-emerald-500 text-white" :
            toast.type === "error" ? "bg-red-600 border-red-500 text-white" :
            "bg-gray-800 border-gray-700 text-white"
          }`}>
            {toast.type === "success" && (
              <svg className="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>
            )}
            {toast.type === "error" && (
              <svg className="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
            )}
            {toast.type === "info" && (
              <svg className="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" /></svg>
            )}
            <span className="text-sm font-medium">{toast.message}</span>
            <button onClick={() => setToast(null)} className="ml-2 text-white/70 hover:text-white transition">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
            </button>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
