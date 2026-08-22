import React from "react";
import { Send, Square, Layers } from "lucide-react";
import { Glass } from "@samasante/liquid-glass";
import VoiceOrb from "./VoiceOrb";
import PromptSuggestions from "./PromptSuggestions";

export default function BottomInputBar({
  textInput,
  onChangeText,
  onSubmit,
  onStop,
  isRecording,
  isLoading,
  audioLevel,
  onToggleRecord,
  selectedStrategy = "sentence_aware",
  onOpenCompare,
  onSelectPrompt,
  onRunJudgeSuite,
}) {
  const strategyLabel =
    selectedStrategy === "sentence_aware"
      ? "Sentence-Aware"
      : selectedStrategy === "fixed_overlap"
      ? "Fixed Overlap"
      : selectedStrategy === "semantic"
      ? "Semantic"
      : "Metadata-Aware";

  return (
    <div
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        paddingBottom: "20px",
        paddingTop: "10px",
        background: "transparent",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        pointerEvents: "none",
      }}
    >
      {/* Suggestions Line */}
      <div style={{ width: "100%", maxWidth: "720px", padding: "0 16px", pointerEvents: "auto" }}>
        <PromptSuggestions
          onSelectPrompt={onSelectPrompt}
          onRunJudgeSuite={onRunJudgeSuite}
          disabled={isLoading || isRecording}
        />
      </div>

      {/* Floating Translucent Glass Lens Capsule */}
      <div style={{ width: "100%", maxWidth: "720px", padding: "0 16px", pointerEvents: "auto" }}>
        <Glass
          optics={{
            depth: 0.9,
            dispersion: 0.35,
            strength: 0.8,
            frost: 22,
            brightness: 0.06,
            specular: 1.6,
            sheen: 1.2,
            glow: 0.45,
            curvature: 0.45,
            bend: 0.3,
            bendWidth: 0.15,
          }}
          radius={999}
          style={{
            width: "100%",
            borderRadius: "999px",
            boxShadow: "0 20px 50px -10px rgba(15, 23, 42, 0.22), 0 0 0 1.5px rgba(255, 255, 255, 0.65)",
          }}
        >
          <form
            onSubmit={onSubmit}
            className="liquid-glass-input"
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "6px 8px 6px 6px",
              borderRadius: "999px",
              boxSizing: "border-box",
            }}
          >
            {/* Liquid Amber Voice Recording Button */}
            <VoiceOrb
              size={42}
              isRecording={isRecording}
              isLoading={isLoading}
              audioLevel={audioLevel}
              onToggleRecord={onToggleRecord}
              disabled={isLoading}
            />

            {/* Text Input */}
            <input
              type="text"
              value={textInput}
              onChange={(e) => onChangeText(e.target.value)}
              placeholder={isRecording ? "Listening to your voice..." : "Ask a factual question in English or Hindi..."}
              disabled={isLoading || isRecording}
              className="font-sans"
              style={{
                flex: 1,
                background: "transparent",
                border: "none",
                outline: "none",
                color: "var(--ink)",
                fontSize: "15.5px",
                fontWeight: 700,
                minWidth: 0,
              }}
            />

            {/* Strategy Selector Pill */}
            <button
              type="button"
              onClick={onOpenCompare}
              title="Click to benchmark all 4 chunking strategies"
              className="liquid-glass-btn strategy-pill-btn font-accent"
              style={{
                padding: "6px 14px",
                fontSize: "12.5px",
                fontWeight: 700,
                color: "var(--ink)",
                gap: "5px",
                flexShrink: 0,
              }}
            >
              <Layers size={13} color="var(--sun-dark)" />
              <span className="hidden sm:inline">{strategyLabel}</span>
            </button>

            {/* Submit / Stop Action Button */}
            {isLoading ? (
              <button
                type="button"
                onClick={onStop}
                className="liquid-glass-btn"
                style={{
                  width: "40px",
                  height: "40px",
                  padding: 0,
                  borderRadius: "50%",
                  backgroundColor: "rgba(254, 226, 226, 0.65)",
                  color: "#DC2626",
                  border: "1.5px solid rgba(239, 68, 68, 0.5)",
                  flexShrink: 0,
                  boxShadow: "0 4px 14px rgba(239, 68, 68, 0.25)",
                }}
                title="Stop generation"
              >
                <Square size={15} fill="currentColor" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!textInput.trim()}
                className="liquid-glass-btn"
                style={{
                  width: "40px",
                  height: "40px",
                  padding: 0,
                  borderRadius: "50%",
                  backgroundColor: textInput.trim() ? "rgba(255, 255, 255, 0.65)" : "rgba(255, 255, 255, 0.25)",
                  color: textInput.trim() ? "var(--ink)" : "var(--ink-soft)",
                  border: textInput.trim() ? "1.5px solid var(--sun)" : "1.5px solid rgba(255, 255, 255, 0.4)",
                  flexShrink: 0,
                  boxShadow: textInput.trim() ? "0 4px 16px rgba(245, 158, 11, 0.35)" : "none",
                  cursor: textInput.trim() ? "pointer" : "default",
                }}
                title="Send query"
              >
                <Send size={15} />
              </button>
            )}
          </form>
        </Glass>
      </div>
    </div>
  );
}
