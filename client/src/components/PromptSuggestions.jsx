import React from "react";
import { Zap, Sparkles } from "lucide-react";
import DatasetQuestionPicker from "./DatasetQuestionPicker";
import { playTactileClick } from "../utils/sound";

const QUICK_TOPICS = [
  {
    label: "Manhattan Project",
    query: "Who directed the Los Alamos Laboratory during the Manhattan Project?",
  },
  {
    label: "मैनहट्टन परियोजना",
    query: "मैनहट्टन परियोजना कब शुरू हुई थी?",
  },
  {
    label: "SQL Sysdate",
    query: "how to use sysdate in sql",
  },
  {
    label: "Masala Omelette",
    query: "How to make a masala omelette step by step?",
  },
];

export default function PromptSuggestions({ onSelectPrompt, onRunJudgeSuite, disabled }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "10px",
        flexWrap: "wrap",
        marginBottom: "12px",
        userSelect: "none",
      }}
    >
      {/* 1. Primary Feature: Dataset Question Dropdown with EN/HI Switcher */}
      <DatasetQuestionPicker onSelectPrompt={onSelectPrompt} disabled={disabled} />

      {/* 2. Judge Benchmark Suite Action Button */}
      {onRunJudgeSuite && (
        <button
          type="button"
          onClick={() => {
            playTactileClick();
            onRunJudgeSuite();
          }}
          disabled={disabled}
          className="liquid-glass-btn font-accent"
          title="Run sequential 3-stage live benchmark on real pipeline (English In-Domain, Hindi In-Domain, Out-of-Domain)"
          style={{
            padding: "6px 16px",
            fontSize: "13px",
            fontWeight: 800,
            color: "#92400E",
            backgroundColor: "rgba(254, 243, 199, 0.85)",
            border: "1.5px solid var(--sun)",
            gap: "5px",
            boxShadow: "0 2px 10px rgba(245, 158, 11, 0.25)",
            cursor: disabled ? "not-allowed" : "pointer",
          }}
        >
          <Zap size={14} fill="currentColor" color="var(--sun-dark)" />
          <span>⚡ Run Judge Suite</span>
        </button>
      )}

      {/* Divider */}
      <div
        style={{
          width: "1px",
          height: "18px",
          backgroundColor: "rgba(0, 0, 0, 0.15)",
          display: "inline-block",
        }}
      />

      {/* 3. Quick Chips */}
      <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
        {QUICK_TOPICS.map((item, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => {
              playTactileClick();
              !disabled && onSelectPrompt(item.query);
            }}
            disabled={disabled}
            className="liquid-glass-btn font-accent"
            style={{
              fontSize: "12.5px",
              fontWeight: 700,
              padding: "5px 12px",
              color: "var(--ink)",
            }}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
}
