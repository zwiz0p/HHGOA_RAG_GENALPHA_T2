import { useVoiceCapture } from "../hooks/useVoiceCapture";

export default function VoiceRecorder({ onAudioReady, disabled }) {
  const { isRecording, startRecording, stopRecording } = useVoiceCapture();

  async function handleClick() {
    if (disabled) return;
    if (isRecording) {
      const blob = await stopRecording();
      if (blob) {
        onAudioReady(blob);
      } else {
        onAudioReady(null, "Audio recording was too short or silent. Please try speaking again.");
      }
    } else {
      try {
        await startRecording();
      } catch (err) {
        onAudioReady(null, "Microphone permission was denied or unavailable in this browser.");
      }
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      style={{
        padding: "16px 32px",
        borderRadius: "999px",
        border: "none",
        background: isRecording ? "#EA3378" : "#2C663A",
        color: "#F7F3E8",
        fontSize: "16px",
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
        transition: "all 0.2s ease",
        boxShadow: isRecording
          ? "0 0 20px rgba(234, 51, 120, 0.5)"
          : "0 4px 12px rgba(44, 102, 58, 0.3)",
      }}
    >
      {isRecording ? "⏹ Stop Recording" : "🎙 Ask a question"}
    </button>
  );
}

