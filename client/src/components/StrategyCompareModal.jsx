import React from "react";
import { X, Layers, CheckCircle2, AlertTriangle, ArrowRight } from "lucide-react";

export default function StrategyCompareModal({ isOpen, onClose, data, loading, query }) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(15, 23, 42, 0.35)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "20px",
      }}
      onClick={onClose}
    >
      <div
        className="liquid-glass-card"
        style={{
          maxWidth: "960px",
          width: "100%",
          maxHeight: "88vh",
          overflowY: "auto",
          padding: "32px",
          position: "relative",
          textAlign: "left",
          backgroundColor: "rgba(255, 255, 255, 0.75)",
          backdropFilter: "blur(40px) saturate(200%)",
          WebkitBackdropFilter: "blur(40px) saturate(200%)",
          border: "1.5px solid rgba(255, 255, 255, 0.85)",
          boxShadow: "0 32px 80px -10px rgba(15, 23, 42, 0.30), 0 10px 25px rgba(0,0,0,0.12)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
          <div>
            <div
              className="liquid-badge-amber font-accent"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                padding: "3px 12px",
                fontSize: "13px",
                fontWeight: 700,
                marginBottom: "8px",
                borderRadius: "999px",
              }}
            >
              <Layers size={13} />
              <span>HACKATHON REQUIREMENT #2</span>
            </div>
            <h2 className="font-display" style={{ margin: "2px 0 6px", color: "var(--ink)", fontSize: "28px" }}>
              Multi-Strategy Chunking Evaluation Matrix
            </h2>
            <p className="font-accent" style={{ margin: 0, color: "var(--ink-soft)", fontSize: "16px", fontWeight: 700 }}>
              Evaluating boundary preservation, token counts, retrieval quality, and latency across 4 chunking architectures.
            </p>
          </div>
          <button
            onClick={onClose}
            className="liquid-glass-btn"
            style={{
              width: "36px",
              height: "36px",
              padding: 0,
            }}
          >
            <X size={18} color="var(--ink)" />
          </button>
        </div>

        {/* Query Evaluated */}
        <div
          className="liquid-glass-subtle font-sans"
          style={{
            padding: "12px 16px",
            marginBottom: "20px",
            fontSize: "14px",
            color: "var(--ink)",
          }}
        >
          <span style={{ fontWeight: 800 }}>Active Query: </span>
          <span style={{ fontStyle: "italic", fontWeight: 600 }}>"{query || data?.query}"</span>
        </div>

        {loading ? (
          <div className="font-sans" style={{ padding: "60px 0", textAlign: "center", color: "var(--ink)", fontSize: "16px", fontWeight: 700 }}>
            Running 4-way parallel chunking, embedding, and cross-encoder evaluation...
          </div>
        ) : data?.results ? (
          <div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
                gap: "18px",
                marginBottom: "20px",
              }}
            >
              {Object.entries(data.results).map(([key, item]) => {
                const isDefault = item.is_production_default;
                return (
                  <div
                    key={key}
                    className="liquid-glass-card font-sans"
                    style={{
                      border: isDefault ? "2px solid var(--mint)" : "1.5px solid rgba(255, 255, 255, 0.70)",
                      backgroundColor: isDefault ? "rgba(220, 252, 231, 0.60)" : "rgba(255, 255, 255, 0.50)",
                      backdropFilter: "blur(24px) saturate(180%)",
                      WebkitBackdropFilter: "blur(24px) saturate(180%)",
                      padding: "20px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                        <span style={{ fontSize: "16px", fontWeight: 800, color: "var(--ink)" }}>{item.strategy_name}</span>
                        {isDefault && (
                          <span
                            className="liquid-badge-green font-accent"
                            style={{
                              fontSize: "12px",
                              fontWeight: 800,
                              padding: "2px 10px",
                              borderRadius: "999px",
                            }}
                          >
                            PRODUCTION DEFAULT
                          </span>
                        )}
                      </div>
                      <p style={{ fontSize: "13px", color: "var(--ink-soft)", margin: "0 0 14px", fontWeight: 600 }}>{item.description}</p>

                      <div
                        style={{
                          display: "flex",
                          gap: "8px",
                          flexWrap: "wrap",
                          marginBottom: "14px",
                          fontSize: "12px",
                        }}
                      >
                        <span
                          className="mono-metric liquid-glass-subtle"
                          style={{
                            padding: "4px 10px",
                            color: "var(--ink)",
                            fontWeight: 800,
                          }}
                        >
                          {item.latency_ms} ms
                        </span>
                        <span
                          className="mono-metric liquid-glass-subtle"
                          style={{
                            padding: "4px 10px",
                            color: "var(--ink)",
                            fontWeight: 800,
                          }}
                        >
                          {item.token_count} tokens
                        </span>
                        <span
                          style={{
                            backgroundColor: item.boundary_intact ? "rgba(220, 252, 231, 0.95)" : "rgba(255, 237, 213, 0.95)",
                            color: item.boundary_intact ? "var(--mint)" : "var(--terracotta)",
                            border: item.boundary_intact ? "1px solid rgba(34, 197, 94, 0.4)" : "1px solid rgba(234, 88, 12, 0.4)",
                            padding: "4px 10px",
                            borderRadius: "8px",
                            fontWeight: 800,
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                          }}
                        >
                          {item.boundary_intact ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
                          <span>{item.boundary_intact ? "Boundary Intact" : "Clipped Mid-Sentence"}</span>
                        </span>
                        <span
                          className="mono-metric"
                          style={{
                            backgroundColor: "rgba(254, 243, 199, 0.95)",
                            border: "1px solid rgba(245, 158, 11, 0.4)",
                            color: "var(--sun-dark)",
                            padding: "4px 10px",
                            borderRadius: "8px",
                            fontWeight: 800,
                          }}
                        >
                          {(item.score !== undefined ? item.score : (item.confidence * 100)).toFixed(1)}% score
                        </span>
                      </div>

                      <div
                        className="font-mono"
                        style={{
                          backgroundColor: "rgba(255, 255, 255, 0.7)",
                          border: "1px solid rgba(0, 0, 0, 0.08)",
                          borderRadius: "12px",
                          padding: "10px 12px",
                          fontSize: "12px",
                          color: "var(--ink)",
                          lineHeight: "1.5",
                          maxHeight: "90px",
                          overflowY: "auto",
                        }}
                      >
                        "{item.top_chunk}"
                      </div>
                    </div>

                    {item.metadata_tags && (
                      <div style={{ marginTop: "12px", fontSize: "11.5px", color: "var(--ink-soft)", fontWeight: 700 }}>
                        Tags: has_digit: {item.metadata_tags.has_digit ? "Yes" : "No"}, doc_id: {item.metadata_tags.chunk_id}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div
              className="liquid-glass-subtle font-sans"
              style={{
                backgroundColor: "rgba(220, 252, 231, 0.85)",
                border: "1.5px solid rgba(34, 197, 94, 0.4)",
                padding: "16px 20px",
                fontSize: "14px",
                color: "var(--ink)",
                lineHeight: 1.5,
              }}
            >
              <strong>Architectural Conclusion: </strong> {data.recommendation}
            </div>
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "30px", color: "var(--terracotta)", fontWeight: 700 }}>
            Failed to load comparison metrics. Please try again.
          </div>
        )}
      </div>
    </div>
  );
}
