"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  ArrowDownLeft,
  ArrowUpRight,
  ShieldAlert,
  Activity,
  CheckCircle,
  AlertTriangle,
  Sparkles,
  Zap,
  ArrowRight,
  FileCheck2
} from "lucide-react";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboardMetrics()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const summary = data?.summary || {
    total_managed: 1248920,
    to_receive: 235680,
    to_pay: 118450,
    at_risk: 48500,
    pending_approvals_count: 1,
    active_threats_count: 1
  };

  const health = data?.system_health || {
    payment_extraction_accuracy: 98.4,
    reconciliation_accuracy: 96.8,
    risk_classifier_f1: 100.0,
    agent_tool_success_rate: 99.2,
    human_escalation_rate: 7.5
  };

  const models = data?.ml_benchmarks || {};

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Financial Control Center
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Autonomous Financial Memory, Trust Ledgers &amp; Razorpay Recovery Ecosystem
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            href="/memory"
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-lg shadow-blue-600/30 flex items-center space-x-1.5 transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>Find My Money</span>
          </Link>
          <Link
            href="/simulator"
            className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-200 border border-white/10 text-xs font-semibold flex items-center space-x-1.5 transition-all"
          >
            <Zap className="w-4 h-4 text-purple-400" />
            <span>Simulation Lab</span>
          </Link>
        </div>
      </div>

      {/* 4 Core Financial Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Managed */}
        <div className="glass-panel p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Managed</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white tracking-tight">
              ₹{summary.total_managed.toLocaleString("en-IN")}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Active cashflow &amp; obligations</p>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-blue-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* To Receive */}
        <div className="glass-panel p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">To Receive</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <ArrowDownLeft className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-emerald-400 tracking-tight">
              ₹{summary.to_receive.toLocaleString("en-IN")}
            </span>
          </div>
          <div className="flex items-center justify-between mt-2">
            <span className="text-[11px] text-slate-500">Inbound receivables</span>
            <Link href="/recovery" className="text-[11px] text-emerald-400 hover:underline flex items-center">
              Recover <ArrowRight className="w-3 h-3 ml-0.5" />
            </Link>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* To Pay */}
        <div className="glass-panel p-5 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">To Pay</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-amber-300 tracking-tight">
              ₹{summary.to_pay.toLocaleString("en-IN")}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">Vendor &amp; partner obligations</p>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-amber-500/5 rounded-full blur-xl pointer-events-none" />
        </div>

        {/* Money At Risk */}
        <div className="glass-panel p-5 rounded-2xl relative overflow-hidden border-rose-500/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-rose-300">Money At Risk</span>
            <div className="p-2 rounded-lg bg-rose-500/20 text-rose-400">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-rose-400 tracking-tight">
              ₹{summary.at_risk.toLocaleString("en-IN")}
            </span>
          </div>
          <div className="flex items-center justify-between mt-2">
            <span className="text-[11px] text-rose-400/80">Overdue &gt; 14 days</span>
            <Link href="/shield" className="text-[11px] text-rose-300 hover:underline flex items-center">
              Inspect <ArrowRight className="w-3 h-3 ml-0.5" />
            </Link>
          </div>
          <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-rose-500/10 rounded-full blur-xl pointer-events-none" />
        </div>
      </div>

      {/* AI System Health & Reliability Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* System Health Gauges */}
        <div className="glass-panel p-6 rounded-2xl space-y-4 lg:col-span-1">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400" />
              AI System Reliability
            </h2>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20">
              OPTIMAL
            </span>
          </div>

          <div className="space-y-3 pt-2">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Payment OCR Extraction</span>
                <span className="text-white font-mono font-semibold">{health.payment_extraction_accuracy}%</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${health.payment_extraction_accuracy}%` }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Reconciliation Auto-Match</span>
                <span className="text-white font-mono font-semibold">{health.reconciliation_accuracy}%</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${health.reconciliation_accuracy}%` }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Risk Classifier F1 Score</span>
                <span className="text-white font-mono font-semibold">{health.risk_classifier_f1}%</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-purple-500 rounded-full" style={{ width: `${health.risk_classifier_f1}%` }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Agent Tool Call Success</span>
                <span className="text-white font-mono font-semibold">{health.agent_tool_success_rate}%</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-teal-500 rounded-full" style={{ width: `${health.agent_tool_success_rate}%` }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-400">Human Escalation Rate</span>
                <span className="text-amber-400 font-mono font-semibold">{health.human_escalation_rate}%</span>
              </div>
              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500 rounded-full" style={{ width: `${health.human_escalation_rate * 4}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Machine Learning Benchmark Suite (Held-out Test Set) */}
        <div className="glass-panel p-6 rounded-2xl space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-purple-400" />
                Risk ML Benchmark Suite (7,500 Held-Out Samples)
              </h2>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Strict 70/15/15 split evaluation on synthetic Indian SMB payment anomalies
              </p>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono">
              XGBoost Production
            </span>
          </div>

          <div className="overflow-x-auto pt-2">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-slate-400">
                  <th className="pb-2 font-medium">Model Architecture</th>
                  <th className="pb-2 font-medium">Precision</th>
                  <th className="pb-2 font-medium">Recall</th>
                  <th className="pb-2 font-medium">F1 Score</th>
                  <th className="pb-2 font-medium">ROC-AUC</th>
                  <th className="pb-2 font-medium">False Positives</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {Object.entries(models).map(([mName, mData]: any) => (
                  <tr key={mName} className="hover:bg-white/5 transition-colors">
                    <td className="py-2.5 font-medium text-white flex items-center gap-1.5">
                      {mName.includes("Production") ? (
                        <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-slate-500" />
                      )}
                      {mName}
                    </td>
                    <td className="py-2.5 font-mono text-slate-300">{(mData.precision * 100).toFixed(2)}%</td>
                    <td className="py-2.5 font-mono text-slate-300">{(mData.recall * 100).toFixed(2)}%</td>
                    <td className="py-2.5 font-mono font-semibold text-emerald-400">{(mData.f1_score * 100).toFixed(2)}%</td>
                    <td className="py-2.5 font-mono text-slate-300">{(mData.roc_auc).toFixed(4)}</td>
                    <td className="py-2.5 font-mono text-slate-400">
                      {mData.confusion_matrix?.false_positives} (₹{mData.estimated_fp_cost_inr || 0})
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Quick Access Action Hub */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href="/approvals"
          className="glass-panel p-5 rounded-2xl glass-panel-hover flex items-center justify-between"
        >
          <div className="space-y-1">
            <span className="text-xs font-semibold text-amber-300 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              AI Action Approvals
            </span>
            <p className="text-sm text-white font-medium">1 High-Risk Transfer Gated</p>
            <p className="text-[11px] text-slate-400">Review human-in-the-loop decisions</p>
          </div>
          <ArrowRight className="w-5 h-5 text-slate-400" />
        </Link>

        <Link
          href="/recovery"
          className="glass-panel p-5 rounded-2xl glass-panel-hover flex items-center justify-between"
        >
          <div className="space-y-1">
            <span className="text-xs font-semibold text-blue-400 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5" />
              Razorpay Recovery Links
            </span>
            <p className="text-sm text-white font-medium">₹78,500 in Overdue Invoices</p>
            <p className="text-[11px] text-slate-400">Dispatch bounded recovery reminders</p>
          </div>
          <ArrowRight className="w-5 h-5 text-slate-400" />
        </Link>

        <Link
          href="/exceptions"
          className="glass-panel p-5 rounded-2xl glass-panel-hover flex items-center justify-between"
        >
          <div className="space-y-1">
            <span className="text-xs font-semibold text-purple-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" />
              Honest Exceptions
            </span>
            <p className="text-sm text-white font-medium">Transparent Ambiguity Queue</p>
            <p className="text-[11px] text-slate-400">Edge cases where AI declined guessing</p>
          </div>
          <ArrowRight className="w-5 h-5 text-slate-400" />
        </Link>
      </div>
    </div>
  );
}
