import React from "react";

export const CHUNKING_OPTIONS = [
  { id: "sentence_aware", name: "Sentence-Aware (Default)", desc: "94.7% boundary preservation" },
  { id: "fixed_overlap", name: "Fixed Overlap (120 tok)", desc: "Sliding window with redundancy" },
  { id: "semantic", name: "Semantic (Embedding Drift)", desc: "Topic-shift boundary cuts" },
  { id: "metadata_aware", name: "Metadata-Aware", desc: "Language & entity decorated" },
];

export default function ChunkingSelector({ selectedStrategy, onSelect, onOpenCompare }) {
  return (
    <div
      className="liquid-glass-subtle"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "8px 16px",
        margin: "0 auto 24px",
        maxWidth: "640px",
        fontSize: "13px",
        flexWrap: "wrap",
        gap: "10px",
        border: "1px solid rgba(255, 255, 255, 0.08)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span style={{ fontWeight: 600, color: "#94A3B8", fontSize: "12px" }}>Chunking Architecture:</span>
        <select
          value={selectedStrategy}
          onChange={(e) => onSelect(e.target.value)}
          style={{
            padding: "5px 10px",
            borderRadius: "8px",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            background: "rgba(15, 23, 42, 0.8)",
            color: "#F1F5F9",
            fontWeight: 500,
            fontSize: "12px",
            cursor: "pointer",
            outline: "none",
            fontFamily: "var(--font-sans)",
          }}
        >
          {CHUNKING_OPTIONS.map((opt) => (
            <option key={opt.id} value={opt.id} style={{ background: "#0F172A", color: "#F1F5F9" }}>
              {opt.name}
            </option>
          ))}
        </select>
      </div>

      <button
        onClick={onOpenCompare}
        type="button"
        style={{
          background: "rgba(99, 102, 241, 0.15)",
          color: "#A5B4FC",
          border: "1px solid rgba(99, 102, 241, 0.35)",
          borderRadius: "8px",
          padding: "6px 12px",
          fontWeight: 600,
          fontSize: "11px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: "6px",
          transition: "all 0.2s ease",
          outline: "none",
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.background = "rgba(99, 102, 241, 0.25)";
          e.currentTarget.style.borderColor = "rgba(99, 102, 241, 0.5)";
          e.currentTarget.style.color = "#C7D2FE";
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.background = "rgba(99, 102, 241, 0.15)";
          e.currentTarget.style.borderColor = "rgba(99, 102, 241, 0.35)";
          e.currentTarget.style.color = "#A5B4FC";
        }}
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
        </svg>
        <span>Compare 4 Strategies</span>
      </button>
    </div>
  );
}
