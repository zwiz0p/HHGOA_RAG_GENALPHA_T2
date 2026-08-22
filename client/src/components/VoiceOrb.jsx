import React from "react";
import { Mic, Square } from "lucide-react";

export default function VoiceOrb({
  isRecording,
  isLoading,
  audioLevel = 0,
  onToggleRecord,
  disabled = false,
  size = 42,
}) {
  const dynamicScale = isRecording ? 1 + audioLevel * 0.35 : 1;

  return (
    <button
      type="button"
      onClick={onToggleRecord}
      disabled={disabled || isLoading}
      aria-label={isRecording ? "Stop voice recording" : "Start voice recording"}
      className="liquid-sun-btn"
      style={{
        width: `${size}px`,
        height: `${size}px`,
        transform: `scale(${dynamicScale})`,
        cursor: disabled || isLoading ? "not-allowed" : "pointer",
        flexShrink: 0,
        padding: 0,
      }}
    >
      {isRecording ? (
        <Square size={14} fill="#14151E" stroke="#14151E" strokeWidth={2} />
      ) : (
        <Mic size={19} color="#14151E" strokeWidth={2.4} />
      )}
    </button>
  );
}
