"use client";

import { Search, Bell, ShieldCheck, ArrowUpRight } from "lucide-react";
import Link from "next/link";

export function Header() {
  return (
    <header className="h-16 border-b border-white/10 bg-[#0a0d14]/80 backdrop-blur-md sticky top-0 z-30 flex items-center justify-between px-8">
      {/* Search Trigger to Memory */}
      <Link 
        href="/memory" 
        className="flex items-center space-x-3 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-slate-400 text-xs w-96 hover:border-blue-500/40 hover:bg-white/10 transition-all cursor-pointer"
      >
        <Search className="w-3.5 h-3.5 text-slate-400" />
        <span>Search Financial Memory (e.g. &apos;Rahul ₹20,000&apos; or UTR)...</span>
        <kbd className="ml-auto text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-slate-400 font-mono">⌘K</kbd>
      </Link>

      {/* Right Tools & Status */}
      <div className="flex items-center space-x-4">
        {/* Razorpay Webhook badge */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-medium">
          <span className="w-2 h-2 rounded-full bg-blue-400" />
          <span>Razorpay Webhook: Active</span>
        </div>

        {/* Quick Simulator CTA */}
        <Link
          href="/simulator"
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all"
        >
          <span>Simulation Lab</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>

        {/* User Avatar */}
        <div className="flex items-center space-x-2.5 pl-2 border-l border-white/10">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-xs font-bold text-white border border-white/20">
            AM
          </div>
          <div className="text-left hidden md:block">
            <p className="text-xs font-semibold text-white leading-tight">Arjun Mehta</p>
            <p className="text-[10px] text-slate-400">Mehta Infrastructure</p>
          </div>
        </div>
      </div>
    </header>
  );
}
