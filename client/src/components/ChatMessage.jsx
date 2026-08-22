import React, { useState, useEffect } from "react";
import { CheckCircle2, Globe, Zap, ChevronDown, BookOpen, AlertCircle, Sparkles, Loader2, Volume2, VolumeX } from "lucide-react";
import { Glass } from "@samasante/liquid-glass";
import AuraStar from "./AuraStar";
import LatencyWaterfall from "./LatencyWaterfall";
import FormattedAnswer from "./FormattedAnswer";
import { speakText, stopSpeech } from "../utils/tts";
import { highlightQueryTerms } from "../utils/highlight";
import { playTactileClick } from "../utils/sound";

export default function ChatMessage({
  message,
  messageIndex,
  onSynthesize,
  onGenerateGeneral,
}) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [isSpeakingLocal, setIsSpeakingLocal] = useState(false);
  const { role, text, streaming, data, synthesizing, synthesisLatency, isVoiceTriggered, userQuery } = message;

  // Assistant Role State Detection
  const isOutOfDomain = data?.source_type === "out_of_domain" || data?.prompt_synthesis;
  const isGeneral = data?.source_type === "general_knowledge" || data?.generation_mode === "general_knowledge";
  const isSynthesized = data?.generation_mode === "conversational_synthesis" || message.isSynthesized;
  const isFastPath = data?.source_type === "fast_path";
  const isExtractive = (data?.generation_mode === "extractive" || data?.source_type === "knowledge_base") && !isSynthesized;

  const cleanAnswer = (text || "")
    .replace(/^⚠️\s*\*Note:[^*]+\*\s*\n*/i, "")
    .replace(/^⚠️\s*\*Not found[^*]+\*\s*\n*/i, "")
    .trim();

  const confPct = data?.confidence ? Math.round(data.confidence * 100) : null;
  const sources = data?.sources || [];
  const queryText = data?.transcript || userQuery || "";

  // Voice Input Auto-Playback: Automatically speak generated answer ONLY when query originated from voice
  useEffect(() => {
    if (
      role === "assistant" &&
      isVoiceTriggered &&
      !streaming &&
      !synthesizing &&
      cleanAnswer &&
      !isOutOfDomain
    ) {
      speakText(
        cleanAnswer,
        () => setIsSpeakingLocal(true),
        () => setIsSpeakingLocal(false)
      );
    }
    return () => {
      stopSpeech();
    };
  }, [streaming, synthesizing, isVoiceTriggered, role, cleanAnswer, isOutOfDomain]);

  function handleToggleTTS() {
    playTactileClick();
    if (isSpeakingLocal) {
      stopSpeech();
      setIsSpeakingLocal(false);
    } else if (cleanAnswer) {
      speakText(
        cleanAnswer,
        () => setIsSpeakingLocal(true),
        () => setIsSpeakingLocal(false)
      );
    }
  }

  if (role === "user") {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "18px" }}>
        <div
          className="liquid-glass-user font-sans"
          style={{
            maxWidth: "82%",
            padding: "14px 20px",
            fontSize: "15px",
            lineHeight: 1.5,
            fontWeight: 700,
          }}
        >
          {text}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", gap: "12px", alignItems: "flex-start", marginBottom: "24px" }}>
      {/* Mini Warm Sun Avatar */}
      <div style={{ flexShrink: 0, marginTop: "6px" }}>
        <AuraStar size={30} isLoading={streaming || synthesizing} />
      </div>

      {/* Assistant Liquid Glass Card */}
      <Glass
        optics={{
          depth: 0.5,
          dispersion: 0.2,
          strength: 0.4,
          frost: 20,
          brightness: 0.08,
          specular: 1.1,
          sheen: 0.7,
          glow: 0.3,
          curvature: 0.25,
          bend: 0.15,
          bendWidth: 0.1,
        }}
        radius={24}
        style={{
          flex: 1,
          maxWidth: "92%",
          borderRadius: "24px",
          boxShadow: "0 20px 48px -8px rgba(15, 23, 42, 0.18), 0 0 0 1.5px rgba(255, 255, 255, 0.85)",
        }}
      >
        <div
          className="liquid-glass-card font-sans"
          style={{
            width: "100%",
            padding: "18px 22px",
            boxSizing: "border-box",
            borderRadius: "24px",
          }}
        >
        {/* Status Mode Badge & Action Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "6px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
            {isFastPath ? (
              <div
                className="liquid-badge-amber font-accent"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "5px",
                  padding: "3px 12px",
                  borderRadius: "999px",
                  fontSize: "12.5px",
                  fontWeight: 700,
                }}
              >
                <Zap size={13} />
                <span>Fast-Path Router (<span className="mono-metric">&lt; 0.1ms</span>)</span>
              </div>
            ) : isOutOfDomain ? (
              <div
                className="font-accent"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "5px",
                  padding: "3px 12px",
                  borderRadius: "999px",
                  fontSize: "12.5px",
                  fontWeight: 700,
                  backgroundColor: "rgba(255, 209, 102, 0.95)",
                  color: "#78350F",
                  border: "1px solid rgba(245, 158, 11, 0.4)",
                }}
              >
                <AlertCircle size={13} />
                <span>Not in Dataset Scope (<span className="mono-metric">&lt; 80ms</span>)</span>
              </div>
            ) : isGeneral ? (
              <div
                className="liquid-badge-orange font-accent"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "5px",
                  padding: "3px 12px",
                  borderRadius: "999px",
                  fontSize: "12.5px",
                  fontWeight: 700,
                }}
              >
                <Globe size={13} />
                <span>General Knowledge Mode</span>
              </div>
            ) : isSynthesized ? (
              <div
                className="liquid-badge-green font-accent"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "5px",
                  padding: "3px 12px",
                  borderRadius: "999px",
                  fontSize: "12.5px",
                  fontWeight: 700,
                }}
              >
                <Sparkles size={13} />
                <span>Conversational Spoken Synthesis</span>
              </div>
            ) : (
              <div
                className="liquid-badge-green font-accent"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "5px",
                  padding: "3px 12px",
                  borderRadius: "999px",
                  fontSize: "12.5px",
                  fontWeight: 700,
                }}
              >
                <CheckCircle2 size={13} />
                <span>Backed by Knowledge Base (Extractive Fast-Path {data?.total_latency_ms ? `${data.total_latency_ms.toFixed(2)}ms` : ""})</span>
              </div>
            )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {/* Speaker / Text-to-Speech (TTS) Button */}
            {cleanAnswer && !isOutOfDomain && (
              <button
                type="button"
                onClick={handleToggleTTS}
                className="liquid-glass-btn"
                title={isSpeakingLocal ? "Stop speaking" : "Listen to answer (Voice-Back)"}
                style={{
                  padding: "4px 10px",
                  borderRadius: "999px",
                  fontSize: "12px",
                  gap: "4px",
                  color: isSpeakingLocal ? "var(--sun-dark)" : "var(--ink)",
                  backgroundColor: isSpeakingLocal ? "rgba(254, 243, 199, 0.95)" : undefined,
                  border: isSpeakingLocal ? "1.5px solid var(--sun)" : undefined,
                }}
              >
                {isSpeakingLocal ? <VolumeX size={14} /> : <Volume2 size={14} />}
                <span>{isSpeakingLocal ? "Stop" : "Listen"}</span>
              </button>
            )}

            {/* Confidence Score Pill */}
            {confPct !== null && !isOutOfDomain && (
              <span
                className="mono-metric"
                style={{
                  fontSize: "12px",
                  fontWeight: 800,
                  color: confPct >= 75 ? "var(--mint)" : "var(--sun-dark)",
                  backgroundColor: "rgba(255, 255, 255, 0.8)",
                  padding: "2px 8px",
                  borderRadius: "6px",
                  border: "1px solid rgba(0,0,0,0.06)",
                }}
              >
                {confPct}% confidence
              </span>
            )}
          </div>
        </div>

        {/* Out of Domain Notice */}
        {isOutOfDomain && !isGeneral && (
          <div
            style={{
              padding: "12px 14px",
              backgroundColor: "rgba(254, 243, 199, 0.95)",
              border: "1px solid rgba(245, 158, 11, 0.35)",
              borderRadius: "14px",
              marginBottom: "14px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#92400E", fontSize: "14px", fontWeight: 700 }}>
              <AlertCircle size={16} />
              <span>This question is not present in the indexed MSMARCO-XI dataset.</span>
            </div>

            {onGenerateGeneral && (
              <button
                type="button"
                onClick={() => {
                  playTactileClick();
                  onGenerateGeneral(messageIndex, queryText);
                }}
                disabled={synthesizing}
                className="liquid-glass-btn font-accent"
                style={{
                  alignSelf: "flex-start",
                  padding: "7px 16px",
                  fontSize: "13px",
                  fontWeight: 700,
                  backgroundColor: "rgba(255, 237, 213, 0.95)",
                  color: "#C2410C",
                  border: "1px solid rgba(234, 88, 12, 0.4)",
                  gap: "6px",
                  cursor: synthesizing ? "wait" : "pointer",
                }}
              >
                {synthesizing ? <Loader2 size={14} className="animate-spin" /> : <Globe size={14} />}
                <span>Answer using General Knowledge</span>
              </button>
            )}
          </div>
        )}

        {/* Text Stream Content with LaTeX & Markdown */}
        {(!isOutOfDomain || isGeneral) && (
          <div style={{ fontSize: "15px", lineHeight: 1.65, color: "var(--ink)", fontWeight: 600 }}>
            {cleanAnswer ? (
              <FormattedAnswer text={cleanAnswer} streaming={streaming || synthesizing} />
            ) : (
              <span>{streaming || synthesizing ? "Generating answer..." : "No answer received."}</span>
            )}
            {(streaming || synthesizing) && <span className="cozy-caret" />}
          </div>
        )}

        {/* In-Domain Extractive Action: Spoken Synthesis Button */}
        {isExtractive && !isFastPath && !streaming && onSynthesize && (
          <div style={{ marginTop: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
            <button
              type="button"
              onClick={() => {
                playTactileClick();
                onSynthesize(messageIndex, queryText, cleanAnswer);
              }}
              disabled={synthesizing}
              className="liquid-glass-btn font-accent"
              style={{
                padding: "7px 16px",
                fontSize: "13px",
                fontWeight: 700,
                color: "var(--ink)",
                backgroundColor: "rgba(220, 252, 231, 0.95)",
                border: "1px solid rgba(34, 197, 94, 0.45)",
                gap: "6px",
                cursor: synthesizing ? "wait" : "pointer",
              }}
            >
              {synthesizing ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} color="var(--mint)" />}
              <span>Generate Voice-Friendly Spoken Synthesis</span>
            </button>
          </div>
        )}

        {/* Sources Drawer with In-Passage Query Term Highlighting */}
        {sources && sources.length > 0 && !isGeneral && !isFastPath && (
          <div style={{ marginTop: "14px", borderTop: "1px dashed rgba(42, 33, 24, 0.15)", paddingTop: "10px" }}>
            <button
              type="button"
              onClick={() => {
                playTactileClick();
                setSourcesOpen(!sourcesOpen);
              }}
              className="font-accent"
              style={{
                background: "transparent",
                border: "none",
                color: "var(--ink)",
                fontSize: "13.5px",
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "5px",
                padding: 0,
                outline: "none",
              }}
            >
              <BookOpen size={14} color="var(--ink-soft)" />
              <span>{sourcesOpen ? "Hide Sources" : `Check the Sources (${sources.length} Passages)`}</span>
              <ChevronDown
                size={14}
                style={{
                  transform: sourcesOpen ? "rotate(180deg)" : "rotate(0deg)",
                  transition: "transform 0.2s ease",
                }}
              />
            </button>

            {sourcesOpen && (
              <div style={{ marginTop: "10px", display: "flex", flexDirection: "column", gap: "8px" }}>
                {sources.map((s, idx) => (
                  <div
                    key={s.chunk_id || idx}
                    className="liquid-glass-subtle font-sans"
                    style={{
                      padding: "10px 14px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px", fontSize: "11.5px" }}>
                      <span className="font-mono" style={{ fontWeight: 700, color: "var(--ink-soft)" }}>Passage {idx + 1} ({s.chunk_strategy || "sentence_aware"})</span>
                      {s.rerank_score !== undefined && (
                        <span className="mono-metric" style={{ color: "var(--mint)", fontWeight: 800 }}>
                          Score: {typeof s.rerank_score === "number" ? s.rerank_score.toFixed(2) : s.rerank_score}
                        </span>
                      )}
                    </div>
                    {/* Highlight Query Terms in Retrieved Passage */}
                    <div style={{ margin: 0, fontSize: "13px", color: "var(--ink)", lineHeight: 1.5, fontWeight: 500 }}>
                      {highlightQueryTerms(s.text, queryText)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Telemetry Stage Receipts */}
        {data?.timings_ms && (
          <LatencyWaterfall
            timings={data.timings_ms}
            totalLatency={data.total_latency_ms}
            source_type={data.source_type}
            generation_mode={data.generation_mode}
            synthesisLatency={synthesisLatency}
          />
        )}
        </div>
      </Glass>
    </div>
  );
}
