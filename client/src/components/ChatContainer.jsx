import React, { useRef, useEffect } from "react";
import ChatMessage from "./ChatMessage";

export default function ChatContainer({
  messages = [],
  isRecording = false,
  isLoading = false,
  audioLevel = 0,
  onSelectPrompt,
  onSynthesize,
  onGenerateGeneral,
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const isEmpty = messages.length === 0 && !isLoading;

  const quickPrompts = [
    {
      label: "Manhattan Project",
      sub: "In-Domain Extractive",
      query: "Who directed the Los Alamos Laboratory during the Manhattan Project?",
      tint: "rgba(255, 255, 255, 0.25)",
    },
    {
      label: "मैनहट्टन परियोजना",
      sub: "In-Domain Hindi",
      query: "मैनहट्टन परियोजना कब शुरू हुई थी?",
      tint: "rgba(187, 247, 208, 0.25)",
    },
    {
      label: "Masala Omelette",
      sub: "General Knowledge",
      query: "How to make a masala omelette step by step?",
      tint: "rgba(253, 230, 138, 0.25)",
    },
  ];

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
      {isEmpty ? (
        /* Empty State Hero */
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "36px 16px 190px",
            textAlign: "center",
          }}
        >
          {/* Prominent AURA Title Graphic Asset */}
          <img
            src="/assets/aura-title.png"
            alt="AURA"
            style={{
              width: "clamp(260px, 38vw, 420px)",
              height: "auto",
              objectFit: "contain",
              filter: "drop-shadow(0 16px 36px rgba(0, 0, 0, 0.25))",
              marginBottom: "14px",
              userSelect: "none",
            }}
          />

          {/* Sub-70ms tagline — frosted pill for contrast */}
          <div
            className="font-accent"
            style={{
              display: "inline-block",
              margin: "0 auto 30px",
              padding: "10px 22px",
              maxWidth: "560px",
              borderRadius: "999px",
              background: "rgba(255, 255, 255, 0.45)",
              backdropFilter: "blur(18px) saturate(180%)",
              WebkitBackdropFilter: "blur(18px) saturate(180%)",
              border: "1px solid rgba(255, 255, 255, 0.6)",
              boxShadow:
                "0 4px 18px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.7)",
            }}
          >
            <p
              style={{
                color: "#1a1a1a",
                fontSize: "17.5px",
                fontWeight: 700,
                margin: 0,
                lineHeight: 1.4,
              }}
            >
              Sub-70ms extractive voice retrieval with on-demand spoken synthesis
            </p>
          </div>

          {/* Quick Prompt Glass Cards */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "14px", justifyContent: "center", maxWidth: "600px" }}>
            {quickPrompts.map((p, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectPrompt(p.query)}
                style={{
                  padding: "18px 24px",
                  cursor: "pointer",
                  background: `linear-gradient(135deg, ${p.tint}, rgba(255,255,255,0.08))`,
                  backdropFilter: "blur(28px) saturate(200%) brightness(1.08)",
                  WebkitBackdropFilter: "blur(28px) saturate(200%) brightness(1.08)",
                  border: "1.5px solid rgba(255, 255, 255, 0.65)",
                  boxShadow:
                    "0 10px 32px rgba(0, 0, 0, 0.14), inset 0 1.5px 0 rgba(255, 255, 255, 0.85), inset 0 -1px 8px rgba(255, 255, 255, 0.25)",
                  textAlign: "left",
                  display: "flex",
                  flexDirection: "column",
                  gap: "3px",
                  outline: "none",
                  borderRadius: "20px",
                  minWidth: "170px",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease",
                  isolation: "isolate",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-3px) scale(1.02)";
                  e.currentTarget.style.boxShadow =
                    "0 16px 40px rgba(0, 0, 0, 0.18), inset 0 1.5px 0 rgba(255, 255, 255, 0.9), inset 0 -1px 8px rgba(255, 255, 255, 0.3)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0) scale(1)";
                  e.currentTarget.style.boxShadow =
                    "0 10px 32px rgba(0, 0, 0, 0.14), inset 0 1.5px 0 rgba(255, 255, 255, 0.85), inset 0 -1px 8px rgba(255, 255, 255, 0.25)";
                }}
              >
                <span className="font-sans" style={{ fontSize: "15px", fontWeight: 800, color: "var(--ink)" }}>{p.label}</span>
                <span className="font-accent" style={{ fontSize: "13px", color: "var(--ink-soft)", fontWeight: 700 }}>{p.sub}</span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* Active Chat Message Stream */
        <div style={{ flex: 1, padding: "16px 4px 190px" }}>
          {messages.map((msg, idx) => (
            <ChatMessage
              key={idx}
              message={msg}
              messageIndex={idx}
              onSynthesize={onSynthesize}
              onGenerateGeneral={onGenerateGeneral}
            />
          ))}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
} 