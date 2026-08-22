export default function TranscriptDisplay({ transcript }) {
  if (!transcript) return null;
  return (
    <p style={{ fontStyle: "italic", color: "#555", margin: "16px 0" }}>
      "{transcript}"
    </p>
  );
}
