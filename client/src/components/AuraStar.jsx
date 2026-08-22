import React from "react";

export default function AuraStar({
  size = 28,
  isRecording = false,
  isLoading = false,
  audioLevel = 0,
  className = "",
}) {
  const dynamicScale = isRecording ? 1 + audioLevel * 0.35 : 1;

  return (
    <div
      className={className}
      style={{
        position: "relative",
        width: `${size}px`,
        height: `${size}px`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          transform: `scale(${dynamicScale})`,
          transition: isRecording ? "transform 0.08s ease-out" : "all 0.3s ease",
          animation: isLoading ? "cozyCaretBlink 1s infinite" : "none",
          filter: "drop-shadow(0 2px 8px rgba(244, 183, 64, 0.45))",
        }}
      >
        <defs>
          <linearGradient id="cozySunGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FFE9A8" />
            <stop offset="55%" stopColor="#F4B740" />
            <stop offset="100%" stopColor="#D8562F" />
          </linearGradient>
        </defs>

        {/* Soft Sun Ray Petals / Star */}
        <path
          d="M 50 2 C 50 24, 76 50, 98 50 C 76 50, 50 76, 50 98 C 50 76, 24 50, 2 50 C 24 50, 50 24, 50 2 Z"
          fill="url(#cozySunGrad)"
        />

        {/* Center Glow */}
        <circle cx="50" cy="50" r="14" fill="#FFFFFF" opacity="0.85" />
        <circle cx="50" cy="50" r="8" fill="#F4B740" />
      </svg>
    </div>
  );
}
