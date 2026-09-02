"use client";

import { useState, useEffect } from "react";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ShieldAlert,
  Send,
  User,
  ArrowRight,
  Sparkles
} from "lucide-react";
import { api } from "@/lib/api";

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [decisionFeedback, setDecisionFeedback] = useState<string | null>(null);

  const loadApprovals = () => {
    api.getPendingApprovals()
      .then((data) => {
        setApprovals(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadApprovals();
  }, []);

  const handleDecision = async (id: string, decision: string) => {
    try {
      const res = await api.decideApproval(id, decision);
      setDecisionFeedback(res.message);
      loadApprovals();
      setTimeout(() => setDecisionFeedback(null), 4000);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <CheckCircle2 className="w-6 h-6 text-blue-400" />
          AI Actions Waiting For Your Approval
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Human-in-the-loop guardrails: AI investigates and prepares actions; you authorize sensitive money movements and communications.
        </p>
      </div>

      {decisionFeedback && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          {decisionFeedback}
        </div>
      )}

      {/* Approvals List */}
      <div className="space-y-4">
        {approvals.map((req) => (
          <div
            key={req.id}
            className={`glass-panel p-6 rounded-2xl space-y-4 border-l-4 ${
              req.severity === "CRITICAL" || req.severity === "HIGH"
                ? "border-l-rose-500 bg-rose-500/5"
                : "border-l-amber-500 bg-amber-500/5"
            }`}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-bold text-white">{req.title}</h3>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                    req.severity === "HIGH" || req.severity === "CRITICAL"
                      ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                      : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                  }`}>
                    {req.severity} PRIORITY
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Target Counterparty: <strong className="text-slate-200">{req.target_entity_name || "Unknown"}</strong>
                </p>
              </div>

              {req.amount && (
                <div className="text-right">
                  <span className="text-xl font-bold font-mono text-white">
                    ₹{req.amount.toLocaleString("en-IN")}
                  </span>
                  <p className="text-[10px] text-slate-500">Action Value</p>
                </div>
              )}
            </div>

            {/* Description & Payload Details */}
            <div className="p-4 rounded-xl bg-black/30 border border-white/5 space-y-2 text-xs">
              <span className="text-slate-400 font-semibold block text-[11px]">AI Findings &amp; Rationale:</span>
              <p className="text-slate-200">{req.description}</p>
              
              {req.payload?.flagged_signals && (
                <div className="flex flex-wrap gap-1.5 pt-2">
                  {req.payload.flagged_signals.map((sig: string, idx: number) => (
                    <span key={idx} className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono">
                      {sig}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => handleDecision(req.id, "reject")}
                className="px-4 py-2 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-all cursor-pointer"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Reject Action</span>
              </button>
              <button
                onClick={() => handleDecision(req.id, "approve")}
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 flex items-center space-x-1.5 transition-all cursor-pointer"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Authorize Action</span>
              </button>
            </div>
          </div>
        ))}

        {approvals.length === 0 && !loading && (
          <div className="glass-panel p-12 rounded-2xl text-center text-slate-400 space-y-2">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
            <p className="text-base font-medium text-white">All AI Actions Reviewed</p>
            <p className="text-xs text-slate-500">There are no pending approvals requiring human authorization.</p>
          </div>
        )}
      </div>
    </div>
  );
}
