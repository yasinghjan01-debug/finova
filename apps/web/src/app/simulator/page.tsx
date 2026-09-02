"use client";

import { useState } from "react";
import {
  FlaskConical,
  Play,
  ShieldAlert,
  RotateCcw,
  UploadCloud,
  CheckCircle2,
  Clock,
  Zap,
  ArrowRight
} from "lucide-react";
import { api } from "@/lib/api";

export default function SimulatorPage() {
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [simResult, setSimResult] = useState<any>(null);

  const runSimulation = async (scenario: string) => {
    setActiveScenario(scenario);
    setRunning(true);
    setSimResult(null);

    try {
      let res;
      if (scenario === "impersonation") {
        res = await api.runSimImpersonation();
      } else if (scenario === "recovery") {
        res = await api.runSimRecovery();
      } else if (scenario === "ocr") {
        res = await api.runSimOCR();
      }
      setSimResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <FlaskConical className="w-6 h-6 text-purple-400" />
          FINOVA Simulation Lab
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Live scenario execution environment for evaluating end-to-end autonomous loops and risk telemetry.
        </p>
      </div>

      {/* 3 Scenario Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Scenario 1: Impersonation Attack */}
        <div className={`glass-panel p-6 rounded-2xl space-y-4 border-2 transition-all ${
          activeScenario === "impersonation" ? "border-rose-500 bg-rose-500/5 shadow-lg shadow-rose-500/10" : "hover:border-white/20"
        }`}>
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-xl bg-rose-500/20 text-rose-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-mono font-bold">
              SCENARIO 1
            </span>
          </div>

          <div>
            <h3 className="text-base font-bold text-white">Impersonation Attack</h3>
            <p className="text-xs text-slate-400 mt-1">
              Malicious actor poses as &apos;Rahul Sharma&apos; demanding urgent ₹75,000 to a new VPA from an unverified number.
            </p>
          </div>

          <button
            onClick={() => runSimulation("impersonation")}
            disabled={running}
            className="w-full py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md shadow-rose-600/30 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{running && activeScenario === "impersonation" ? "Simulating Attack..." : "Execute Attack Defense"}</span>
          </button>
        </div>

        {/* Scenario 2: Revenue Recovery */}
        <div className={`glass-panel p-6 rounded-2xl space-y-4 border-2 transition-all ${
          activeScenario === "recovery" ? "border-emerald-500 bg-emerald-500/5 shadow-lg shadow-emerald-500/10" : "hover:border-white/20"
        }`}>
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400">
              <RotateCcw className="w-5 h-5" />
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-mono font-bold">
              SCENARIO 2
            </span>
          </div>

          <div>
            <h3 className="text-base font-bold text-white">Revenue Recovery Loop</h3>
            <p className="text-xs text-slate-400 mt-1">
              Overdue invoice detection $\rightarrow$ Razorpay link generation $\rightarrow$ Webhook confirmation $\rightarrow$ ₹0 balance.
            </p>
          </div>

          <button
            onClick={() => runSimulation("recovery")}
            disabled={running}
            className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{running && activeScenario === "recovery" ? "Running Recovery..." : "Execute Recovery Loop"}</span>
          </button>
        </div>

        {/* Scenario 3: Screenshot OCR */}
        <div className={`glass-panel p-6 rounded-2xl space-y-4 border-2 transition-all ${
          activeScenario === "ocr" ? "border-blue-500 bg-blue-500/5 shadow-lg shadow-blue-500/10" : "hover:border-white/20"
        }`}>
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-xl bg-blue-500/20 text-blue-400">
              <UploadCloud className="w-5 h-5" />
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-mono font-bold">
              SCENARIO 3
            </span>
          </div>

          <div>
            <h3 className="text-base font-bold text-white">Screenshot OCR to Memory</h3>
            <p className="text-xs text-slate-400 mt-1">
              Simulate Google Pay screenshot upload $\rightarrow$ UTR extraction $\rightarrow$ Entity Resolution $\rightarrow$ Auto-reconcile.
            </p>
          </div>

          <button
            onClick={() => runSimulation("ocr")}
            disabled={running}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 flex items-center justify-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{running && activeScenario === "ocr" ? "Parsing Proof..." : "Execute OCR Ingestion"}</span>
          </button>
        </div>
      </div>

      {/* Simulation Telemetry Step-by-Step Viewer */}
      {simResult && (
        <div className="glass-panel p-6 rounded-2xl space-y-5 border-purple-500/30">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-400" />
              Live Execution Telemetry: {simResult.scenario}
            </h2>
            <span className="text-xs font-bold font-mono px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 uppercase">
              STATUS: {simResult.attack_status || simResult.status || "COMPLETED"}
            </span>
          </div>

          {/* Timeline of Steps */}
          <div className="space-y-3 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/10">
            {simResult.steps?.map((step: any, idx: number) => (
              <div key={idx} className="flex items-start space-x-4 relative pl-8">
                <div className="w-2.5 h-2.5 rounded-full bg-purple-400 absolute left-[7px] top-1.5 border-2 border-[#0a0d14]" />
                <div className="flex-1 p-3 rounded-xl bg-white/5 border border-white/5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{step.event}</span>
                    <span className="text-[10px] font-mono text-slate-500">{step.time}</span>
                  </div>
                  <p className="text-slate-300 mt-1 font-mono text-[11px]">{step.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
