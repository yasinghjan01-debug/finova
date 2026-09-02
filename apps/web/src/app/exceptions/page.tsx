"use client";

import { useState, useEffect } from "react";
import {
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  FileQuestion,
  UserPlus,
  ArrowRight,
  ShieldCheck
} from "lucide-react";
import { api } from "@/lib/api";

export default function ExceptionsPage() {
  const [exceptions, setExceptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getHonestExceptions()
      .then((data) => {
        setExceptions(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <AlertCircle className="w-6 h-6 text-purple-400" />
          Honest Exceptions — When AI Declines to Guess
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          High-trust fintech engineering: Rather than hallucinating or forcing matches, FINOVA transparently surfaces ambiguous edge-cases.
        </p>
      </div>

      {/* Exception Banner */}
      <div className="p-5 rounded-2xl glass-panel bg-purple-500/5 border-purple-500/20 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Controlled Autonomy Standard</h3>
            <p className="text-xs text-slate-400">
              Only matches exceeding 95% confidence with verified entities are auto-reconciled.
            </p>
          </div>
        </div>
        <span className="text-xs font-mono font-bold text-purple-300 bg-purple-500/20 px-3 py-1.5 rounded-xl border border-purple-500/30">
          {exceptions.length} Cases Requiring Review
        </span>
      </div>

      {/* Exceptions Grid */}
      <div className="space-y-4">
        {exceptions.map((exc) => (
          <div
            key={exc.id}
            className="glass-panel p-5 rounded-2xl glass-panel-hover space-y-3 border-l-4 border-l-purple-500"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-bold text-white">{exc.title}</h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-mono font-semibold uppercase">
                    {exc.reason_category}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">{exc.description}</p>
              </div>

              <div className="text-right">
                <span className="text-xl font-bold font-mono text-white">
                  ₹{exc.amount.toLocaleString("en-IN")}
                </span>
                <p className="text-[10px] text-slate-500">UTR: {exc.utr}</p>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-white/5 text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-purple-400" />
                Suggested Action: <strong className="text-slate-200">{exc.suggested_action}</strong>
              </span>

              <button className="px-4 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all cursor-pointer">
                Resolve Case
              </button>
            </div>
          </div>
        ))}

        {exceptions.length === 0 && !loading && (
          <div className="glass-panel p-10 rounded-2xl text-center text-slate-400 space-y-2">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
            <p className="text-base font-medium text-white">No Exceptions Found</p>
            <p className="text-xs text-slate-500">All received payments have been successfully reconciled to known counterparties and obligations.</p>
          </div>
        )}
      </div>
    </div>
  );
}
