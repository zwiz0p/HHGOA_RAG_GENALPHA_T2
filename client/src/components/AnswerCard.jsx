import React, { useState } from "react";

export default function AnswerCard({ result }) {
  const [sourcesOpen, setSourcesOpen] = useState(false);

  if (!result) return null;

  const {
    answer,
    transcript,
    confidence,
    sources = [],
    grounded,
    blocked,
    block_reason,
    source_type,
    streaming,
  } = result;

  const isGeneral = source_type === "general_knowledge" || (!grounded && !blocked && !source_type?.includes("fast"));
  const isFastPath = source_type === "fast_path";
  const isGrounded = source_type === "knowledge_base" || (grounded && !blocked);

  // Clean answer text by removing raw prefix tags if they were included by backend
  const cleanAnswer = (answer || "")
    .replace(/^⚠️\s*\*Note:[^*]+\*\s*\n*/i, "")
    .replace(/^⚠️\s*\*Not found[^*]+\*\s*\n*/i, "")
    .trim();

  // Confidence percentage formatting
  const confPct = confidence ? Math.round(confidence * 100) : null;

  return (
    <div
      className="liquid-glass"
      style={{
        margin: "24px auto",
        maxWidth: "680px",
        textAlign: "left",
        padding: "24px",
        position: "relative",
        overflow: "hidden",
        border: isGeneral
          ? "1px solid rgba(245, 158, 11, 0.3)"
          : isFastPath
          ? "1px solid rgba(168, 85, 247, 0.3)"
          : "1px solid rgba(16, 185, 129, 0.25)",
        boxShadow: isGeneral
          ? "0 20px 50px rgba(0, 0, 0, 0.4), 0 0 30px rgba(245, 158, 11, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.15)"
          : isFastPath
          ? "0 20px 50px rgba(0, 0, 0, 0.4), 0 0 30px rgba(168, 85, 247, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.15)"
          : "0 20px 50px rgba(0, 0, 0, 0.4), 0 0 30px rgba(16, 185, 129, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.15)",
      }}
    >
      {/* Top Header Badge Row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "8px" }}>
        {isFastPath ? (
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "4px 10px",
              borderRadius: "999px",
              background: "rgba(168, 85, 247, 0.12)",
              border: "1px solid rgba(168, 85, 247, 0.3)",
              fontSize: "11px",
              fontWeight: 600,
              color: "#C084FC",
              letterSpacing: "0.3px",
            }}
          >
            <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#C084FC", boxShadow: "0 0 6px #C084FC" }} />
            <span>Conversational Fast-Path (&lt; 1 ms)</span>
          </div>
        ) : isGeneral ? (
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "4px 10px",
              borderRadius: "999px",
              background: "rgba(245, 158, 11, 0.12)",
              border: "1px solid rgba(245, 158, 11, 0.3)",
              fontSize: "11px",
              fontWeight: 600,
              color: "#FBBF24",
              letterSpacing: "0.3px",
            }}
          >
            <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#FBBF24", boxShadow: "0 0 6px #FBBF24" }} />
            <span>General Knowledge Response</span>
          </div>
        ) : (
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "4px 10px",
              borderRadius: "999px",
              background: "rgba(16, 185, 129, 0.12)",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              fontSize: "11px",
              fontWeight: 600,
              color: "#34D399",
              letterSpacing: "0.3px",
            }}
          >
            <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#34D399", boxShadow: "0 0 6px #34D399" }} />
            <span>
              Grounded in MSMARCO-XI {confPct ? `(Confidence: ${confPct}%)` : ""}
            </span>
          </div>
        )}

        {/* Query Language or Status */}
        {transcript && (
          <div style={{ fontSize: "11px", color: "#64748B", fontFamily: "var(--font-mono)" }}>
            Query: "{transcript.length > 35 ? transcript.slice(0, 35) + "..." : transcript}"
          </div>
        )}
      </div>

      {/* General Knowledge Fallback Microcopy Alert */}
      {isGeneral && (
        <div
          className="liquid-glass-subtle"
          style={{
            padding: "10px 14px",
            marginBottom: "16px",
            border: "1px solid rgba(245, 158, 11, 0.2)",
            background: "rgba(245, 158, 11, 0.04)",
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: "2px" }}>
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span style={{ fontSize: "12px", color: "#FDE68A", lineHeight: 1.5 }}>
            This topic was not found in the indexed MSMARCO-XI dataset. Answering from general world knowledge.
          </span>
        </div>
      )}

      {/* Answer Body Text */}
      <div style={{ fontSize: "15px", lineHeight: 1.7, color: "#F1F5F9", whiteSpace: "pre-wrap", fontWeight: 400 }}>
        {cleanAnswer || (streaming ? "Searching and synthesizing answer..." : "No answer received.")}
        {streaming && <span className="blinking-cursor" />}
      </div>

      {/* Grounded Source Drawer (Only for Knowledge Base Mode) */}
      {sources && sources.length > 0 && !isGeneral && !isFastPath && (
        <div style={{ marginTop: "20px", borderTop: "1px solid rgba(255, 255, 255, 0.08)", paddingTop: "14px" }}>
          <button
            type="button"
            onClick={() => setSourcesOpen(!sourcesOpen)}
            style={{
              background: "transparent",
              border: "none",
              color: "#94A3B8",
              fontSize: "12px",
              fontWeight: 500,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "0",
              outline: "none",
            }}
          >
            <span>{sourcesOpen ? "Hide Retrieved Passages" : `View Retrieved Passages (${sources.length})`}</span>
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ transform: sourcesOpen ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s ease" }}
            >
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>

          {sourcesOpen && (
            <div style={{ marginTop: "12px", display: "flex", flexDirection: "column", gap: "10px" }}>
              {sources.map((s, idx) => (
                <div
                  key={s.chunk_id || idx}
                  className="liquid-glass-subtle"
                  style={{
                    padding: "12px 14px",
                    border: "1px solid rgba(255, 255, 255, 0.05)",
                    background: "rgba(0, 0, 0, 0.25)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px", fontSize: "11px", color: "#64748B" }}>
                    <span style={{ fontFamily: "var(--font-mono)", color: "#94A3B8" }}>Source {idx + 1} ({s.chunk_strategy || "sentence_aware"})</span>
                    {s.rerank_score !== undefined && (
                      <span className="mono-metric" style={{ color: "#10B981" }}>
                        Score: {typeof s.rerank_score === "number" ? s.rerank_score.toFixed(2) : s.rerank_score}
                      </span>
                    )}
                  </div>
                  <p style={{ margin: 0, fontSize: "13px", color: "#CBD5E1", lineHeight: 1.5 }}>
                    {s.text}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
