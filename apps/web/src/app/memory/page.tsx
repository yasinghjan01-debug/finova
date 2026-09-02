"use client";

import { useState, useEffect } from "react";
import {
  Search,
  Sparkles,
  UploadCloud,
  FileCheck,
  CheckCircle2,
  Calendar,
  Hash,
  User,
  ArrowRight,
  ShieldCheck,
  FileText
} from "lucide-react";
import { api } from "@/lib/api";

export default function MemoryPage() {
  const [query, setQuery] = useState("Rahul ₹20,000");
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  // OCR Ingest state
  const [proofText, setProofText] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ocrResult, setOcrResult] = useState<any>(null);

  const handleSearch = async (searchTerm = query) => {
    if (!searchTerm.trim()) return;
    setLoading(true);
    try {
      const res = await api.findMyMoney(searchTerm);
      setResults(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handleSearch("Rahul ₹20,000");
  }, []);

  const handleIngestProof = async () => {
    if (!proofText.trim()) return;
    setIngesting(true);
    try {
      const res = await api.ingestProof(proofText);
      setOcrResult(res);
      // Refresh search
      handleSearch(query);
    } catch (err) {
      console.error(err);
    } finally {
      setIngesting(false);
    }
  };

  const loadSampleProof = () => {
    setProofText(
      "Google Pay\nPayment to Arjun Mehta Successful\nAmount: ₹30,000.00\nFrom: Rahul Sharma (rahul.sharma@okhdfcbank)\nUPI Ref / UTR: 729104829103\nDate: 01 Sep 2026\nNote: Final settlement for Construction Advance"
    );
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <Sparkles className="w-6 h-6 text-blue-400" />
          Financial Memory &amp; &quot;Find My Money&quot;
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Unstructured payment proofs transformed into canonical, searchable relationship objects.
        </p>
      </div>

      {/* Hero Search Bar */}
      <div className="glass-panel p-4 rounded-2xl border-blue-500/20 shadow-xl shadow-blue-500/5">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          className="flex items-center space-x-3"
        >
          <div className="relative flex-1">
            <Search className="w-5 h-5 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across Amount, Person, Phone, 12-digit UTR, Purpose, or conversation context..."
              className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all font-medium"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold shadow-lg shadow-blue-600/30 flex items-center space-x-2 transition-all cursor-pointer disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>{loading ? "Searching Memory..." : "Find My Money"}</span>
          </button>
        </form>

        {/* Quick Suggestion Pills */}
        <div className="flex items-center space-x-2 mt-3 pt-3 border-t border-white/5 text-xs text-slate-400">
          <span className="text-[11px] text-slate-500">Quick queries:</span>
          {["Rahul ₹20,000", "UTR 8921", "Anita", "Construction advance", "Google Pay"].map((q) => (
            <button
              key={q}
              onClick={() => {
                setQuery(q);
                handleSearch(q);
              }}
              className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-[11px] border border-white/5 transition-all"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Search Results & Ingestion Box */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Search Results Column (2 Cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">
              Memory Matches ({results?.total_matches || 0})
            </h2>
            {results && (
              <span className="text-xs text-slate-400">
                Matched Volume: <strong className="text-emerald-400 font-mono">₹{results.total_amount_matched?.toLocaleString("en-IN")}</strong>
              </span>
            )}
          </div>

          <div className="space-y-3">
            {results?.matches?.map((match: any) => (
              <div
                key={match.payment_id}
                className="glass-panel p-5 rounded-2xl glass-panel-hover space-y-3 border-l-4 border-l-blue-500"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xl font-bold text-white font-mono">
                        ₹{match.amount.toLocaleString("en-IN")}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-semibold border border-blue-500/20">
                        {match.source}
                      </span>
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        {match.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                      <User className="w-3 h-3 text-slate-500" />
                      From: <strong className="text-slate-200">{match.person_name}</strong>
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono text-slate-400 flex items-center gap-1 justify-end">
                      <Calendar className="w-3 h-3 text-slate-500" />
                      {match.payment_date}
                    </span>
                    <span className="text-[11px] text-purple-400 font-mono">
                      Match Confidence: {(match.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {/* Purpose & UTR Details */}
                <div className="p-3 rounded-xl bg-black/20 border border-white/5 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[10px]">UTR / RRN Reference</span>
                    <span className="font-mono text-slate-200 font-semibold">{match.utr_rrn || "Not specified"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Matched Obligation</span>
                    <span className="text-slate-200">{match.matched_obligation || "General Ledger Settlement"}</span>
                  </div>
                </div>

                {/* Evidence Snippet */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                  <span className="flex items-center gap-1 text-slate-400">
                    <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                    Evidence: {match.evidence_snippet}
                  </span>
                  {match.proof_available && (
                    <span className="text-blue-400 font-medium">Proof On Record</span>
                  )}
                </div>
              </div>
            ))}

            {results?.matches?.length === 0 && (
              <div className="glass-panel p-8 rounded-2xl text-center text-slate-400 space-y-2">
                <Search className="w-8 h-8 text-slate-500 mx-auto" />
                <p className="text-sm font-medium text-white">No memory records found</p>
                <p className="text-xs text-slate-500">Try searching by person name, ₹ amount, or 12-digit UTR reference.</p>
              </div>
            )}
          </div>
        </div>

        {/* Screenshot Proof Ingestion Column (1 Col) */}
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <UploadCloud className="w-4 h-4 text-blue-400" />
              Ingest Payment Proof (OCR)
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Paste raw OCR text from WhatsApp, SMS, or a payment screenshot to extract UTR, resolve counterparty identity, and update ledgers.
          </p>

          <div className="space-y-3">
            <textarea
              rows={6}
              value={proofText}
              onChange={(e) => setProofText(e.target.value)}
              placeholder="e.g. Paid ₹30,000 to Arjun Mehta\nFrom: Rahul Sharma\nUPI Ref: 729104829103..."
              className="w-full p-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-blue-500 font-mono"
            />
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={loadSampleProof}
                className="text-[11px] text-blue-400 hover:underline cursor-pointer"
              >
                + Load Sample Google Pay Proof
              </button>
              <button
                onClick={handleIngestProof}
                disabled={ingesting || !proofText.trim()}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 flex items-center space-x-1.5 transition-all disabled:opacity-50 cursor-pointer"
              >
                <FileCheck className="w-3.5 h-3.5" />
                <span>{ingesting ? "Parsing..." : "Extract & Save"}</span>
              </button>
            </div>
          </div>

          {/* OCR Parsing Extraction Card */}
          {ocrResult && (
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2 mt-4 text-xs">
              <div className="flex items-center justify-between text-emerald-400 font-semibold">
                <span>Proof Successfully Ingested</span>
                <span>{(ocrResult.entity_confidence * 100).toFixed(1)}% Confidence</span>
              </div>
              <p className="text-slate-300">{ocrResult.proof_summary}</p>
              <div className="space-y-1 text-[11px] text-slate-400 pt-2 border-t border-emerald-500/20">
                <p>• Extracted Amount: <strong className="text-white">₹{ocrResult.extracted_amount?.toLocaleString("en-IN")}</strong></p>
                <p>• UTR Ref: <strong className="text-white font-mono">{ocrResult.extracted_utr || "N/A"}</strong></p>
                <p>• Resolved Counterparty: <strong className="text-white">{ocrResult.matched_person_name || "Unknown"}</strong></p>
                <p>• Auto-Reconciliation: <strong className="text-emerald-400">{ocrResult.auto_reconciled ? "Matched to Obligation" : "Saved to Unallocated Ledger"}</strong></p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
