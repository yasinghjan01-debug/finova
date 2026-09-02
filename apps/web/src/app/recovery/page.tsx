"use client";

import { useState, useEffect } from "react";
import {
  RotateCcw,
  Zap,
  CheckCircle2,
  Clock,
  Send,
  ExternalLink,
  ShieldAlert,
  AlertTriangle,
  ArrowRight
} from "lucide-react";
import { api } from "@/lib/api";

export default function RecoveryPage() {
  const [atRisk, setAtRisk] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [dispatchingId, setDispatchingId] = useState<string | null>(null);
  const [lastDispatched, setLastDispatched] = useState<any>(null);

  const loadData = () => {
    api.getReceivablesAtRisk()
      .then((data) => {
        setAtRisk(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDispatch = async (obligationId: string) => {
    setDispatchingId(obligationId);
    try {
      const res = await api.dispatchRecovery(obligationId);
      setLastDispatched(res);
      loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setDispatchingId(null);
    }
  };

  const totalAtRisk = atRisk.reduce((acc, curr) => acc + (curr.remaining_amount || 0), 0);

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <RotateCcw className="w-6 h-6 text-emerald-400" />
            Razorpay Revenue Recovery Engine
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Detects receivables at risk, selects optimal communication interventions, and creates Razorpay payment links.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-right">
          <span className="text-[11px] text-emerald-300 font-medium block">Total Outstanding at Risk</span>
          <span className="text-xl font-bold font-mono text-emerald-400">
            ₹{totalAtRisk.toLocaleString("en-IN")}
          </span>
        </div>
      </div>

      {/* Dispatched Notification Card */}
      {lastDispatched && (
        <div className="p-5 rounded-2xl glass-panel border-emerald-500/30 bg-emerald-500/5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              {lastDispatched.auto_dispatched ? "Autonomous Reminder Dispatched" : "Queued in AI Approval Center"}
            </span>
            {lastDispatched.payment_link && (
              <a
                href={lastDispatched.payment_link}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-blue-400 hover:underline flex items-center gap-1"
              >
                Inspect Razorpay Link <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
          <p className="text-xs text-slate-300">{lastDispatched.message}</p>
          <p className="text-[11px] text-slate-400 font-mono bg-black/30 p-2 rounded-lg border border-white/5">
            Draft: {lastDispatched.draft_message}
          </p>
        </div>
      )}

      {/* Receivables List */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-slate-300">
          Identified Receivables Requiring Recovery ({atRisk.length})
        </h2>

        <div className="grid grid-cols-1 gap-4">
          {atRisk.map((item) => (
            <div
              key={item.obligation_id}
              className="glass-panel p-5 rounded-2xl glass-panel-hover space-y-4 border-l-4 border-l-emerald-500"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-base font-bold text-white">{item.title}</h3>
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-white/10">
                      {item.person_name}
                    </span>
                    <span className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
                      item.urgency === "HIGH" ? "bg-rose-500/20 text-rose-300 border border-rose-500/30" : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                    }`}>
                      {item.suggested_intervention.replace(/_/g, " ")}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Due Date: <strong className="text-slate-200">{item.due_date}</strong> (Overdue by {item.days_overdue} days)
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-xl font-bold font-mono text-emerald-400">
                    ₹{item.remaining_amount.toLocaleString("en-IN")}
                  </span>
                  <p className="text-[10px] text-slate-500">
                    Total: ₹{item.total_amount.toLocaleString("en-IN")}
                  </p>
                </div>
              </div>

              {/* AI Prepared Draft Message */}
              <div className="p-3.5 rounded-xl bg-black/20 border border-white/5 space-y-1.5 text-xs">
                <div className="flex items-center justify-between text-slate-400 text-[11px]">
                  <span>AI-Prepared Intervention Message</span>
                  <span>Contact Trust Score: <strong className="text-emerald-400">{item.trust_score}/100</strong></span>
                </div>
                <p className="text-slate-200">{item.draft_message}</p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-1 text-xs">
                <span className="text-slate-500 text-[11px]">
                  Policy: {item.remaining_amount <= 50000 ? "Eligible for 1-click / Autonomous Dispatch" : "Requires Human Approval Gate"}
                </span>
                <button
                  onClick={() => handleDispatch(item.obligation_id)}
                  disabled={dispatchingId === item.obligation_id}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-md shadow-emerald-600/30 flex items-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{dispatchingId === item.obligation_id ? "Generating Link..." : "Dispatch Recovery Link"}</span>
                </button>
              </div>
            </div>
          ))}

          {atRisk.length === 0 && !loading && (
            <div className="glass-panel p-8 rounded-2xl text-center text-slate-400">
              🎉 No overdue receivables found! All obligations are reconciled.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
