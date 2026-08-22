export default function LatencyBadge({ timings, total }) {
  if (!timings) return null;

  return (
    <details style={{ marginTop: 12, fontSize: 12, color: "#666" }}>
      <summary style={{ cursor: "pointer" }}>Latency: {total?.toFixed(1)}ms total</summary>
      <ul>
        {Object.entries(timings).map(([stage, ms]) => (
          <li key={stage}>
            {stage}: {ms.toFixed(1)}ms
          </li>
        ))}
      </ul>
    </details>
  );
}
