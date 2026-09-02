"use client";

import { useState, useEffect } from "react";
import {
  Users,
  Shield,
  TrendingUp,
  Clock,
  ArrowDownLeft,
  ArrowUpRight,
  Phone,
  QrCode,
  Tag,
  CheckCircle,
  AlertCircle,
  FileText
} from "lucide-react";
import { api } from "@/lib/api";

export default function PeoplePage() {
  const [people, setPeople] = useState<any[]>([]);
  const [selectedPerson, setSelectedPerson] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPeople()
      .then((data) => {
        setPeople(data);
        if (data.length > 0) {
          loadPersonDetail(data[0].id);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const loadPersonDetail = async (id: string) => {
    try {
      const card = await api.getPersonCard(id);
      setSelectedPerson(card);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Users className="w-6 h-6 text-blue-400" />
          Financial Relationship Graph &amp; Trust Profiles
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Entity resolution maps fragmented aliases into structured counterparties with living trust scores and running ledgers.
        </p>
      </div>

      {/* 2-Column Split: People Master List & Selected Detail Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: People Roster */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-300">Counterparties &amp; Partners</h2>
          <div className="space-y-2">
            {people.map((p) => {
              const isSelected = selectedPerson?.id === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => loadPersonDetail(p.id)}
                  className={`w-full text-left p-4 rounded-2xl glass-panel transition-all cursor-pointer ${
                    isSelected ? "border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/10" : "hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white">{p.canonical_name}</h3>
                      <p className="text-[11px] text-slate-400 capitalize">{p.category}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-bold font-mono text-emerald-400">
                        ₹{p.outstanding_balance.toLocaleString("en-IN")}
                      </span>
                      <p className="text-[10px] text-slate-500">Outstanding</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 mt-3 pt-2 border-t border-white/5 text-[11px]">
                    <span className="text-slate-400">Trust Score:</span>
                    <span className={`font-semibold font-mono ${p.trust_score >= 80 ? "text-emerald-400" : (p.trust_score >= 60 ? "text-amber-400" : "text-rose-400")}`}>
                      {p.trust_score}/100
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="text-slate-400">Reliability: {p.payment_reliability}%</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Selected Relationship Detail Card */}
        <div className="lg:col-span-2 space-y-6">
          {selectedPerson ? (
            <div className="space-y-6">
              {/* Profile Card Header */}
              <div className="glass-panel p-6 rounded-2xl space-y-5">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center space-x-3.5">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-lg font-bold text-white shadow-lg shadow-blue-600/30">
                      {selectedPerson.canonical_name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        {selectedPerson.canonical_name}
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-semibold border border-blue-500/20 uppercase">
                          {selectedPerson.category}
                        </span>
                      </h2>
                      <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
                        <span className="flex items-center gap-1">
                          <Phone className="w-3 h-3 text-slate-500" />
                          {selectedPerson.primary_phone || "No phone"}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <QrCode className="w-3 h-3 text-slate-500" />
                          {selectedPerson.primary_vpa || "No VPA"}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Trust Score Gauge */}
                  <div className="p-3 rounded-xl bg-black/30 border border-white/5 text-right">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Trust Metric</span>
                    <span className="text-2xl font-bold font-mono text-emerald-400">
                      {selectedPerson.trust_score}<span className="text-xs text-slate-500">/100</span>
                    </span>
                  </div>
                </div>

                {/* 3 Metric Summary Banner */}
                <div className="grid grid-cols-3 gap-3 p-4 rounded-xl bg-black/20 border border-white/5 text-center">
                  <div>
                    <span className="text-[10px] text-slate-400 block">Total Given / Invoiced</span>
                    <span className="text-sm font-bold font-mono text-white">
                      ₹{selectedPerson.total_given.toLocaleString("en-IN")}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Total Received</span>
                    <span className="text-sm font-bold font-mono text-emerald-400">
                      ₹{selectedPerson.total_received.toLocaleString("en-IN")}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block">Net Outstanding</span>
                    <span className="text-sm font-bold font-mono text-amber-300">
                      ₹{selectedPerson.outstanding_balance.toLocaleString("en-IN")}
                    </span>
                  </div>
                </div>

                {/* Multi-Channel Identities */}
                <div className="space-y-2 pt-2">
                  <span className="text-xs font-semibold text-slate-300 block">
                    Resolved Identity Channels ({selectedPerson.identities?.length || 0})
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {selectedPerson.identities?.map((ident: any, idx: number) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-xs text-slate-300 flex items-center gap-1.5"
                      >
                        <Tag className="w-3 h-3 text-blue-400" />
                        <span className="text-[10px] text-slate-400 uppercase">{ident.type}:</span>
                        <strong>{ident.value}</strong>
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Relationship Timeline */}
              <div className="glass-panel p-6 rounded-2xl space-y-4">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Clock className="w-4 h-4 text-blue-400" />
                  Financial Relationship Timeline
                </h3>

                <div className="space-y-3 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/10">
                  {selectedPerson.timeline?.map((item: any, idx: number) => (
                    <div key={idx} className="flex items-start space-x-4 relative pl-8">
                      <div className="w-2.5 h-2.5 rounded-full bg-blue-500 absolute left-[7px] top-1.5 border-2 border-[#0a0d14]" />
                      <div className="flex-1 p-3 rounded-xl bg-white/5 border border-white/5 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white">{item.title}</span>
                          <span className="text-[10px] text-slate-500">{item.date}</span>
                        </div>
                        {item.amount && (
                          <p className="text-xs font-mono font-bold text-emerald-400 mt-1">
                            Amount: ₹{item.amount.toLocaleString("en-IN")}
                          </p>
                        )}
                        {item.utr && (
                          <p className="text-[11px] text-slate-400 font-mono">UTR: {item.utr}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-panel p-8 rounded-2xl text-center text-slate-400">
              Select a counterparty from the list to view their relationship card and trust ledger.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
