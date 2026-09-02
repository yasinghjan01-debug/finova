"use client";

import { useState } from "react";
import {
  MessageSquareText,
  Send,
  Sparkles,
  ShieldCheck,
  User,
  Bot,
  Calendar,
  FileCheck2,
  ArrowRight
} from "lucide-react";
import { api } from "@/lib/api";

export default function AssistantPage() {
  const [messages, setMessages] = useState<any[]>([
    {
      role: "assistant",
      content: "Hello Arjun. I am FINOVA, your Financial Memory Assistant. Every answer I provide is verified against your immutable transaction ledgers and evidence graph. How can I help you today?",
      evidence: []
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (text = input) => {
    if (!text.trim()) return;
    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.askAssistant(text);
      const assistantMsg = {
        role: "assistant",
        content: res.answer,
        evidence: res.evidence || [],
        action_suggested: res.action_suggested
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error querying your Financial Memory.",
          evidence: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sampleQuestions = [
    "How much money does Rahul owe me?",
    "Show all payments received from Rahul",
    "What money is at risk right now?",
    "Find the payment with UTR ending 8921"
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <MessageSquareText className="w-6 h-6 text-blue-400" />
          Ask Your Financial Memory
        </h1>
        <p className="text-sm text-slate-400 mt-0.5">
          Evidence-backed financial AI: Never hallucinates numbers. Every response links directly to verified UTRs and ledgers.
        </p>
      </div>

      {/* Quick Prompts */}
      <div className="flex flex-wrap gap-2">
        {sampleQuestions.map((q) => (
          <button
            key={q}
            onClick={() => handleSend(q)}
            className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs border border-white/5 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <Sparkles className="w-3 h-3 text-blue-400" />
            <span>{q}</span>
          </button>
        ))}
      </div>

      {/* Chat Messages Container */}
      <div className="glass-panel p-6 rounded-2xl min-h-[420px] max-h-[580px] overflow-y-auto space-y-6">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex items-start space-x-3 ${m.role === "user" ? "flex-row-reverse space-x-reverse" : ""}`}
          >
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 ${
              m.role === "user" ? "bg-blue-600 text-white" : "gradient-accent text-white shadow-md shadow-blue-500/20"
            }`}>
              {m.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div className={`max-w-xl space-y-3 ${m.role === "user" ? "text-right" : ""}`}>
              <div className={`p-4 rounded-2xl text-xs leading-relaxed inline-block ${
                m.role === "user"
                  ? "bg-blue-600 text-white rounded-tr-none font-medium"
                  : "bg-white/5 border border-white/10 text-slate-200 rounded-tl-none space-y-2 whitespace-pre-line"
              }`}>
                {m.content}
              </div>

              {/* Evidence Citations */}
              {m.evidence && m.evidence.length > 0 && (
                <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-2 text-left">
                  <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                    Verified Evidence Citations ({m.evidence.length})
                  </span>
                  <div className="space-y-1.5">
                    {m.evidence.map((ev: any, eIdx: number) => (
                      <div key={eIdx} className="p-2 rounded-lg bg-white/5 text-[11px] flex items-center justify-between">
                        <div>
                          <strong className="text-white">{ev.title}</strong>
                          <span className="text-slate-500 block text-[10px]">Date: {ev.date} {ev.utr ? `• UTR: ${ev.utr}` : ""}</span>
                        </div>
                        {ev.amount && (
                          <span className="font-mono font-bold text-emerald-400">
                            ₹{ev.amount.toLocaleString("en-IN")}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center space-x-3 text-xs text-slate-400">
            <div className="w-8 h-8 rounded-xl gradient-accent flex items-center justify-center text-white">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-white/5 border border-white/5 animate-pulse">
              Consulting Financial Memory Graph &amp; UTR Ledgers...
            </div>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="glass-panel p-2.5 rounded-2xl flex items-center space-x-3 border-white/10"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything about your payments, relationships, or money at risk..."
          className="flex-1 bg-transparent px-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none font-medium"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30 flex items-center space-x-1.5 transition-all cursor-pointer disabled:opacity-50"
        >
          <span>Ask</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
