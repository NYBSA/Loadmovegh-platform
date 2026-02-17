"use client";

import { useState } from "react";
import { useAdmin, type AdminRole } from "@/context/AdminContext";

/* ── Menu Structure ──────────────────────────────── */

interface MenuItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  badge?: { text: string; color: string };
  roles?: AdminRole[];
  children?: { key: string; label: string; roles?: AdminRole[] }[];
}

const MENU: { group: string; items: MenuItem[] }[] = [
  {
    group: "Dashboard",
    items: [
      {
        key: "overview",
        label: "Overview",
        icon: (
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25a2.25 2.25 0 0 1-2.25-2.25v-2.25Z" />
        ),
      },
      {
        key: "revenue",
        label: "Revenue",
        icon: (
          <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0 1 15.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 0 1 3 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 0 0-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 0 1-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 0 0 3 15h-.75M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm3 0h.008v.008H18V10.5Zm-12 0h.008v.008H6V10.5Z" />
        ),
        roles: ["super_admin", "admin"],
      },
      {
        key: "loads",
        label: "Load Analytics",
        icon: (
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
        ),
      },
    ],
  },
  {
    group: "Management",
    items: [
      {
        key: "users",
        label: "User Approvals",
        icon: (
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
        ),
        badge: { text: "6", color: "yellow" },
        children: [
          { key: "users", label: "Pending Review" },
          { key: "users-approved", label: "Approved Users", roles: ["super_admin", "admin"] },
          { key: "users-rejected", label: "Rejected Users", roles: ["super_admin", "admin"] },
        ],
      },
      {
        key: "commission",
        label: "Commissions",
        icon: (
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
        ),
        roles: ["super_admin", "admin"],
      },
      {
        key: "regions",
        label: "Regional Map",
        icon: (
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" />
        ),
      },
    ],
  },
  {
    group: "Security",
    items: [
      {
        key: "fraud",
        label: "Fraud Alerts",
        icon: (
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        ),
        badge: { text: "7", color: "red" },
        roles: ["super_admin", "admin", "moderator"],
      },
      {
        key: "compliance",
        label: "Compliance",
        icon: (
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
        ),
        badge: { text: "3", color: "orange" },
        roles: ["super_admin", "admin", "moderator"],
      },
    ],
  },
  {
    group: "System",
    items: [
      {
        key: "settings",
        label: "Settings",
        icon: (
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
        ),
        roles: ["super_admin"],
        children: [
          { key: "settings-general", label: "General" },
          { key: "settings-roles", label: "Roles & Permissions" },
          { key: "settings-api", label: "API Keys" },
          { key: "settings-audit", label: "Audit Log" },
        ],
      },
    ],
  },
];

/* ── Badge colors ────────────────────────────────── */

function badgeClass(color: string) {
  const map: Record<string, string> = {
    red: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400",
    yellow: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400",
    orange: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400",
    green: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400",
    blue: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-400",
  };
  return map[color] || map.blue;
}

/* ── Component ───────────────────────────────────── */

export default function Sidebar() {
  const { user, logout, sidebarOpen, setSidebarOpen, sidebarCollapsed, toggleSidebarCollapsed, activeSection, setActiveSection } = useAdmin();
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(new Set());

  const userRole: AdminRole = user?.role || "viewer";

  function isVisible(roles?: AdminRole[]) {
    if (!roles) return true;
    return roles.includes(userRole);
  }

  function toggleMenu(key: string) {
    setExpandedMenus((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function handleNavClick(key: string) {
    setActiveSection(key);
    setSidebarOpen(false);
  }

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden" onClick={() => setSidebarOpen(false)}>
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
        </div>
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col bg-gray-900 dark:bg-gray-950 border-r border-gray-800 transition-all duration-300 lg:static lg:z-auto ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0 ${sidebarCollapsed ? "w-[72px]" : "w-64"}`}
      >
        {/* ── Header ────────────────────────────────── */}
        <div className={`flex h-16 items-center border-b border-gray-800 ${sidebarCollapsed ? "justify-center px-2" : "justify-between px-4"}`}>
          <a href="https://www.loadmovegh.com" className="flex items-center gap-2.5 min-w-0">
            <img src="/logo.png" alt="LoadMoveGH" width={40} height={40} className="h-9 w-auto object-contain flex-shrink-0" />
            {!sidebarCollapsed && (
              <span className="font-bold text-white text-lg truncate">
                LoadMove<span className="text-brand-400">GH</span>
              </span>
            )}
          </a>
          {!sidebarCollapsed && (
            <button
              onClick={toggleSidebarCollapsed}
              className="hidden lg:flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:text-white hover:bg-gray-800 transition"
              title="Collapse sidebar"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M18.75 19.5l-7.5-7.5 7.5-7.5m-6 15L5.25 12l7.5-7.5" />
              </svg>
            </button>
          )}
          {sidebarCollapsed && (
            <button
              onClick={toggleSidebarCollapsed}
              className="hidden lg:flex absolute -right-3 top-5 h-6 w-6 items-center justify-center rounded-full bg-gray-800 border border-gray-700 text-gray-400 hover:text-white hover:bg-gray-700 transition shadow-md"
              title="Expand sidebar"
            >
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
              </svg>
            </button>
          )}
        </div>

        {/* ── Navigation ────────────────────────────── */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-5 scrollbar-thin">
          {MENU.map((group) => {
            const visibleItems = group.items.filter((i) => isVisible(i.roles));
            if (visibleItems.length === 0) return null;

            return (
              <div key={group.group}>
                {!sidebarCollapsed && (
                  <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-gray-500">
                    {group.group}
                  </p>
                )}
                <div className="space-y-0.5">
                  {visibleItems.map((item) => {
                    const hasChildren = item.children && item.children.length > 0;
                    const isExpanded = expandedMenus.has(item.key);
                    const isActive = activeSection === item.key || (hasChildren && item.children!.some((c) => activeSection === c.key));

                    return (
                      <div key={item.key}>
                        <button
                          onClick={() => {
                            if (hasChildren) {
                              toggleMenu(item.key);
                              if (!isExpanded && item.children![0]) handleNavClick(item.children![0].key);
                            } else {
                              handleNavClick(item.key);
                            }
                          }}
                          className={`group flex w-full items-center rounded-lg transition-all duration-150 ${
                            sidebarCollapsed ? "justify-center px-2 py-2.5" : "gap-3 px-3 py-2.5"
                          } text-sm font-medium ${
                            isActive
                              ? "bg-brand-600/15 text-brand-400 shadow-sm"
                              : "text-gray-400 hover:bg-gray-800/60 hover:text-gray-200"
                          }`}
                          title={sidebarCollapsed ? item.label : undefined}
                        >
                          <svg className={`h-5 w-5 flex-shrink-0 ${isActive ? "text-brand-400" : "text-gray-500 group-hover:text-gray-300"}`} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                            {item.icon}
                          </svg>
                          {!sidebarCollapsed && (
                            <>
                              <span className="truncate">{item.label}</span>
                              {item.badge && (
                                <span className={`ml-auto inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold ${badgeClass(item.badge.color)}`}>
                                  {item.badge.text}
                                </span>
                              )}
                              {hasChildren && (
                                <svg
                                  className={`ml-auto h-4 w-4 text-gray-500 transition-transform ${isExpanded ? "rotate-180" : ""} ${item.badge ? "ml-1.5" : ""}`}
                                  fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
                                </svg>
                              )}
                            </>
                          )}
                        </button>

                        {/* Submenu */}
                        {hasChildren && isExpanded && !sidebarCollapsed && (
                          <div className="ml-5 mt-0.5 space-y-0.5 border-l-2 border-gray-800 pl-3">
                            {item.children!.filter((c) => isVisible(c.roles)).map((child) => (
                              <button
                                key={child.key}
                                onClick={() => handleNavClick(child.key)}
                                className={`flex w-full items-center rounded-md px-3 py-2 text-[13px] font-medium transition ${
                                  activeSection === child.key
                                    ? "text-brand-400 bg-brand-600/10"
                                    : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/40"
                                }`}
                              >
                                {child.label}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </nav>

        {/* ── User Footer ───────────────────────────── */}
        <div className={`border-t border-gray-800 ${sidebarCollapsed ? "p-2" : "p-3"}`}>
          {sidebarCollapsed ? (
            <div className="flex flex-col items-center gap-2">
              <div className="h-9 w-9 rounded-full bg-gradient-to-br from-brand-500 to-emerald-600 flex items-center justify-center text-sm font-bold text-white shadow-md" title={user?.name}>
                {user?.name?.split(" ").map((n) => n[0]).join("").slice(0, 2) || "SA"}
              </div>
              <button onClick={logout} className="h-8 w-8 flex items-center justify-center rounded-lg text-red-400 hover:bg-red-600/10 hover:text-red-300 transition" title="Log out">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" />
                </svg>
              </button>
            </div>
          ) : (
            <div className="space-y-2.5">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-full bg-gradient-to-br from-brand-500 to-emerald-600 flex items-center justify-center text-sm font-bold text-white shadow-md flex-shrink-0">
                  {user?.name?.split(" ").map((n) => n[0]).join("").slice(0, 2) || "SA"}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-white truncate">{user?.name || "System Admin"}</p>
                  <p className="text-[11px] text-gray-500 truncate">{user?.email || "admin@loadmovegh.com"}</p>
                </div>
                <span className="inline-flex items-center rounded-md bg-brand-600/20 px-1.5 py-0.5 text-[10px] font-bold text-brand-400 ring-1 ring-brand-500/30">
                  {(user?.role || "admin").replace("_", " ").toUpperCase().slice(0, 5)}
                </span>
              </div>
              <button
                onClick={logout}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-red-600/10 border border-red-800/20 px-3 py-2 text-sm font-medium text-red-400 hover:bg-red-600/20 hover:text-red-300 transition"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" />
                </svg>
                Log Out
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
