"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  Users,
  ShieldAlert,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
  FlaskConical,
  MessageSquareText,
  FileSpreadsheet,
  Activity,
  Layers
} from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Financial Memory", href: "/memory", icon: Search },
    { name: "People & Relationships", href: "/people", icon: Users },
    { name: "Revenue Recovery", href: "/recovery", icon: RotateCcw },
    { name: "Scam Shield (ML)", href: "/shield", icon: ShieldAlert },
    { name: "AI Action Center", href: "/approvals", icon: CheckCircle2 },
    { name: "Honest Exceptions", href: "/exceptions", icon: AlertCircle },
    { name: "Simulation Lab", href: "/simulator", icon: FlaskConical },
    { name: "Ask Memory AI", href: "/assistant", icon: MessageSquareText },
    { name: "Audit Trail", href: "/audit", icon: FileSpreadsheet },
  ];

  return (
    <aside className="w-64 border-r border-white/10 bg-[#0c101a]/95 flex flex-col h-screen fixed left-0 top-0 z-40">
      {/* Brand Header */}
      <div className="p-5 border-b border-white/10">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg gradient-accent flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
            F
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
              FINOVA
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-semibold border border-blue-500/30">
                TRUST
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-medium">Financial Memory Network</p>
          </div>
        </div>
      </div>

      {/* Engine Status Banner */}
      <div className="mx-4 mt-4 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center space-x-2">
        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-[11px] font-semibold text-emerald-300">
          5 Core Engines Active
        </span>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {links.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-blue-600 text-white shadow-md shadow-blue-600/30"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-400"}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Razorpay Integration Badge */}
      <div className="p-4 border-t border-white/10 bg-black/20">
        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
          <span>Razorpay Integration</span>
          <span className="text-blue-400 font-medium">Test Mode</span>
        </div>
        <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
          <div className="bg-blue-500 h-full w-full" />
        </div>
        <p className="text-[10px] text-slate-500 mt-2">Webhooks: Verified HMAC-SHA256</p>
      </div>
    </aside>
  );
}
