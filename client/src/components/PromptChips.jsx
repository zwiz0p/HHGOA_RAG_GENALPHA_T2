import React from "react";

export const SAMPLE_CHIPS = [
  {
    category: "grounded",
    label: "🇬🇧 Manhattan Project",
    desc: "In-Domain English",
    query: "Who directed the Los Alamos Laboratory during the Manhattan Project?",
  },
  {
    category: "grounded",
    label: "🇮🇳 मैनहट्टन परियोजना",
    desc: "In-Domain Hindi",
    query: "मैनहट्टन परियोजना कब शुरू हुई थी?",
  },

  {
    category: "fast_path",
    label: "💬 Greeting & Identity",
    desc: "Sub-0.05ms Fast Path",
    query: "Hello! Who are you?",
  },
  {
    category: "general",
    label: "🌐 General: भारत की राजधानी",
    desc: "Dual-Mode Fallback",
    query: "भारत की राजधानी क्या है?",
  },
  {
    category: "general",
    label: "🍳 Recipe: Masala Omelette",
    desc: "Out-of-Dataset QA",
    query: "How to make a masala omelette step by step?",
  },
];

export default function PromptChips({ onSelect, disabled }) {
  return (
    <div style={{ margin: "0 auto 20px", maxWidth: "680px" }}>
      <div style={{ fontSize: "12px", color: "#556B5C", fontWeight: 600, marginBottom: "8px", textAlign: "center" }}>
        🎯 1-Click Judge Benchmark Prompts:
      </div>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "8px",
          justifyContent: "center",
        }}
      >
        {SAMPLE_CHIPS.map((chip, idx) => {
          const isGeneral = chip.category === "general";
          const isFastPath = chip.category === "fast_path";

          let badgeColor = "#166534";
          let bg = "#F4F8F4";
          let border = "#CDE0D2";

          if (isGeneral) {
            badgeColor = "#92400E";
            bg = "#FEF9EE";
            border = "#FDE68A";
          } else if (isFastPath) {
            badgeColor = "#6B21A8";
            bg = "#FAF5FF";
            border = "#E9D5FF";
          }

          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelect(chip.query)}
              disabled={disabled}
              style={{
                background: bg,
                border: `1px solid ${border}`,
                borderRadius: "20px",
                padding: "6px 12px",
                fontSize: "12px",
                color: badgeColor,
                fontWeight: 600,
                cursor: disabled ? "not-allowed" : "pointer",
                transition: "all 0.15s ease",
                display: "flex",
                alignItems: "center",
                gap: "4px",
                boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
              }}
              onMouseOver={(e) => {
                if (!disabled) e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseOut={(e) => {
                if (!disabled) e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              <span>{chip.label}</span>
              <span style={{ fontSize: "10px", opacity: 0.75, fontWeight: 400 }}>({chip.desc})</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
