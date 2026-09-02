"use client";

import { useState, useEffect } from "react";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  PhoneCall,
  QrCode,
  Lock,
  ArrowRight,
  ShieldCheck
} from "lucide-react";
import { api } from "@/lib/api";

export default function ShieldPage() {
  const [personName, setPersonName] = useState("Rahul Sharma");
  const [amount, setAmount] = useState("75000");
  const [phone, setPhone] = useState("+919876543999");
  const [vpa, setVpa] = useState("rahul.urgent@upi");
  const [message, setMessage] = useState("Bro urgent medical emergency in family, hospital needs deposit right now! Please send ₹75,000 immediately to rahul.urgent@upi. My old phone is broken, don't call.");
  
  const [evaluating, setEvaluating] = useState(false);
  const [riskResult, setRiskResult] = useState<any>(null);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);

  useEffect(() => {
    api.getRiskEvents().then((data) => setRecentEvents(data)).catch(console.error);
  }, []);

  const handleEvaluate = async () => {
    setEvaluating(true);
    try {
      const res = await api.evaluateRisk({
        person_name: personName,
        amount: parseFloat(amount) || 0,
        request_phone: phone,
        destination_vpa: vpa,
        message_text: message
      });
      setRiskResult(res);
      api.getRiskEvents().then((data) => setRecentEvents(data));
    } catch (err) {
      console.error(err);
    } finally {
      setEvaluating(false);
    }
  };

  const loadImpersonationDemo = () => {
    setPersonName("Rahul Sharma");
    setAmount("75000");
    setPhone("+919876543999");
    setVpa("rahul.urgent@upi");
    setMessage("Bro urgent medical emergency in family, hospital needs deposit right now! Please send ₹75,000 immediately to rahul.urgent@upi. My old phone is broken, don't call.");
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <ShieldAlert className="w-6 h-6 text-rose-400" />
          Scam Shield &amp; Impersonation Defense (ML Engine)
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Real-time transaction risk scoring, destination-change detection, and AI impersonation interceptor.
        </p>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Transaction Input Form (1 Col) */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Inspect Payment Request</h2>
            <button
              onClick={loadImpersonationDemo}
              className="text-[11px] text-purple-400 hover:underline cursor-pointer"
            >
              + Load Impersonation Demo
            </button>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Claimed Counterparty Name</label>
              <input
                type="text"
                value={personName}
                onChange={(e) => setPersonName(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-rose-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Request Amount (₹)</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-rose-500 focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Request Phone Number</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-rose-500 focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Destination UPI VPA</label>
              <input
                type="text"
                value={vpa}
                onChange={(e) => setVpa(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-rose-500 focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Incoming Message / Context</label>
              <textarea
                rows={4}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-white/5 border border-white/10 text-white focus:border-rose-500 focus:outline-none text-xs"
              />
            </div>

            <button
              onClick={handleEvaluate}
              disabled={evaluating}
              className="w-full py-3 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold shadow-lg shadow-rose-600/30 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
            >
              <ShieldAlert className="w-4 h-4" />
              <span>{evaluating ? "Evaluating ML Features..." : "Run Scam Shield ML Assessment"}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Assessment Verdict & Risk Breakdown (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          {riskResult ? (
            <div className={`glass-panel p-6 rounded-2xl space-y-5 border-2 ${
              riskResult.risk_level === "CRITICAL" || riskResult.risk_level === "HIGH"
                ? "border-rose-500/50 bg-rose-500/5"
                : "border-emerald-500/50 bg-emerald-500/5"
            }`}>
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-2xl font-bold tracking-tight font-mono ${
                      riskResult.risk_score >= 70 ? "text-rose-400" : "text-emerald-400"
                    }`}>
                      Risk Score: {riskResult.risk_score}/100
                    </span>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase ${
                      riskResult.risk_level === "CRITICAL" ? "bg-rose-500 text-white" : "bg-emerald-500/20 text-emerald-400"
                    }`}>
                      {riskResult.risk_level} RISK
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    ML Model: XGBoost Ensemble (Probability: {(riskResult.ml_probability * 100).toFixed(2)}%)
                  </p>
                </div>

                <div className="text-right">
                  <span className={`text-xs font-bold px-3 py-1.5 rounded-xl border ${
                    riskResult.requires_approval
                      ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                      : "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                  }`}>
                    {riskResult.requires_approval ? "⚠️ Gated in Approval Center" : "✓ Cleared by Policy"}
                  </span>
                </div>
              </div>

              {/* Signals Flagged */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-300 block">Flagged Signals ({riskResult.flagged_signals.length})</span>
                <div className="flex flex-wrap gap-2">
                  {riskResult.flagged_signals.map((sig: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-lg bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-mono font-semibold"
                    >
                      ⚠️ {sig}
                    </span>
                  ))}
                </div>
              </div>

              {/* Explanation & Recommendation */}
              <div className="p-4 rounded-xl bg-black/40 border border-white/10 space-y-2 text-xs">
                <div>
                  <span className="text-slate-400 font-semibold block text-[11px]">AI Root-Cause Explanation:</span>
                  <p className="text-slate-200 mt-0.5">{riskResult.explanation}</p>
                </div>
                <div className="pt-2 border-t border-white/5">
                  <span className="text-slate-400 font-semibold block text-[11px]">Action Recommendation:</span>
                  <p className="text-rose-400 font-bold mt-0.5">{riskResult.recommendation}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel p-10 rounded-2xl text-center text-slate-400 space-y-2">
              <ShieldCheck className="w-10 h-10 text-slate-500 mx-auto" />
              <p className="text-sm font-medium text-white">Scam Shield Ready</p>
              <p className="text-xs text-slate-500">Fill in transaction parameters or click &apos;+ Load Impersonation Demo&apos; to execute ML assessment.</p>
            </div>
          )}

          {/* Historical Flagged Events */}
          <div className="glass-panel p-6 rounded-2xl space-y-4">
            <h3 className="text-sm font-semibold text-white">Recent Security &amp; Risk Intercepts</h3>
            <div className="space-y-3">
              {recentEvents.map((evt) => (
                <div key={evt.id} className="p-3.5 rounded-xl bg-white/5 border border-white/5 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white">{evt.person_name}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-mono">
                        Score {evt.risk_score} ({evt.risk_level})
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1">{evt.explanation}</p>
                  </div>
                  <div className="text-right pl-4">
                    <span className="text-[10px] text-slate-500 block">{evt.date}</span>
                    <span className="text-[11px] font-semibold text-amber-400 capitalize">{evt.status.replace("_", " ")}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
