"use client";

import { useState, useEffect } from "react";
import {
  FileSpreadsheet,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Terminal,
  Activity
} from "lucide-react";
import { api } from "@/lib/api";

export default function AuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAuditLogs()
      .then((data) => {
        setLogs(data);
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
          <FileSpreadsheet className="w-6 h-6 text-blue-400" />
          Immutable Security &amp; Audit Trail
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Every decision, webhook ingestion, OCR parsing event, ML score, and human authorization is permanently recorded.
        </p>
      </div>

      {/* Audit Logs Table */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            System Events ({logs.length})
          </h2>
          <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono font-semibold border border-emerald-500/20">
            TAMPER-EVIDENT
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/10 text-slate-400">
                <th className="pb-2.5 font-medium">Timestamp</th>
                <th className="pb-2.5 font-medium">Event Type</th>
                <th className="pb-2.5 font-medium">Actor</th>
                <th className="pb-2.5 font-medium">Telemetry Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-mono">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-white/5 transition-colors">
                  <td className="py-3 text-slate-400 text-[11px] whitespace-nowrap">
                    {log.timestamp}
                  </td>
                  <td className="py-3 font-semibold text-blue-400">
                    {log.event_type}
                  </td>
                  <td className="py-3 text-slate-300">
                    <span className="px-2 py-0.5 rounded bg-white/5 text-[10px]">
                      {log.actor}
                    </span>
                  </td>
                  <td className="py-3 text-slate-300 text-[11px]">
                    {JSON.stringify(log.details)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
