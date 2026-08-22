import React from "react";

const SUB_MAP = {
  "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
  "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
  "x": "ₓ", "n": "ₙ", "m": "ₘ", "+": "₊", "-": "₋",
  "a": "ₐ", "e": "ₑ", "o": "ₒ", "i": "ᵢ", "r": "ᵣ",
};

const SUP_MAP = {
  "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
  "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
  "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
  "n": "ⁿ", "x": "ˣ",
};

function toSubscript(str) {
  return str.split("").map((c) => SUB_MAP[c] || c).join("");
}

function toSuperscript(str) {
  return str.split("").map((c) => SUP_MAP[c] || c).join("");
}

/**
 * Converts raw LaTeX math & chemical formulas like `$\text{SO}_2$` or `$\text{NO}_x$` into clean Unicode.
 */
export function cleanLatex(text) {
  if (!text) return "";

  let res = text;

  // 1. Convert specific chemical math tags inside $...$ or raw
  // Handle $\text{NAME}_N$ or $\text{NAME}_{...}$
  res = res.replace(/\$\\text\{([^}]+)\}_\{?([a-zA-Z0-9\+\-]+)\}?\$/g, (_, name, sub) => `${name}${toSubscript(sub)}`);
  res = res.replace(/\\text\{([^}]+)\}_\{?([a-zA-Z0-9\+\-]+)\}?/g, (_, name, sub) => `${name}${toSubscript(sub)}`);
  
  // Handle $\text{NAME}^\text{SUP}$ or $\text{NAME}^N$
  res = res.replace(/\$\\text\{([^}]+)\}\^\{?([a-zA-Z0-9\+\-]+)\}?\$/g, (_, name, sup) => `${name}${toSuperscript(sup)}`);
  res = res.replace(/\\text\{([^}]+)\}\^\{?([a-zA-Z0-9\+\-]+)\}?/g, (_, name, sup) => `${name}${toSuperscript(sup)}`);

  // Handle general $...$ expressions
  res = res.replace(/\$([^$]+)\$/g, (_, expr) => {
    let inner = expr;
    // Replace \text{...} with inner
    inner = inner.replace(/\\text\{([^}]+)\}/g, "$1");
    inner = inner.replace(/\\mathrm\{([^}]+)\}/g, "$1");
    inner = inner.replace(/\\mathbf\{([^}]+)\}/g, "$1");

    // Replace subscripts _{xyz} or _x
    inner = inner.replace(/_\{([^}]+)\}/g, (_, s) => toSubscript(s));
    inner = inner.replace(/_([0-9xnm\+\-])/g, (_, s) => toSubscript(s));

    // Replace superscripts ^{xyz} or ^x
    inner = inner.replace(/\^\{([^}]+)\}/g, (_, s) => toSuperscript(s));
    inner = inner.replace(/\^([0-9xnm\+\-])/g, (_, s) => toSuperscript(s));

    // Common math symbols
    inner = inner.replace(/\\times/g, "×");
    inner = inner.replace(/\\approx/g, "≈");
    inner = inner.replace(/\\pm/g, "±");
    inner = inner.replace(/\\le(q)?/g, "≤");
    inner = inner.replace(/\\ge(q)?/g, "≥");
    inner = inner.replace(/\\neq/g, "≠");
    inner = inner.replace(/\\rightarrow/g, "→");
    inner = inner.replace(/\\leftarrow/g, "←");
    inner = inner.replace(/\\degree/g, "°");
    inner = inner.replace(/\\cdot/g, "·");
    inner = inner.replace(/\\alpha/g, "α");
    inner = inner.replace(/\\beta/g, "β");
    inner = inner.replace(/\\gamma/g, "γ");
    inner = inner.replace(/\\delta/g, "δ");
    inner = inner.replace(/\\pi/g, "π");

    return inner;
  });

  // Handle standalone \text{...} remaining outside $
  res = res.replace(/\\text\{([^}]+)\}/g, "$1");
  res = res.replace(/\\mathrm\{([^}]+)\}/g, "$1");

  return res;
}

/**
 * Parses markdown inline styles (bold, italic, code).
 */
function parseInline(text) {
  if (!text) return [];

  // Match bold **...**, italic *...*, code `...`
  const parts = [];
  let remaining = text;
  let key = 0;

  const regex = /(\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`)/;

  while (remaining) {
    const match = remaining.match(regex);
    if (!match) {
      parts.push(<span key={key++}>{remaining}</span>);
      break;
    }

    const index = match.index;
    if (index > 0) {
      parts.push(<span key={key++}>{remaining.slice(0, index)}</span>);
    }

    if (match[2]) {
      // Bold
      parts.push(<strong key={key++} style={{ fontWeight: 700, color: "var(--ink)" }}>{match[2]}</strong>);
    } else if (match[3]) {
      // Italic
      parts.push(<em key={key++} style={{ fontStyle: "italic" }}>{match[3]}</em>);
    } else if (match[4]) {
      // Code
      parts.push(
        <code
          key={key++}
          className="font-mono"
          style={{
            backgroundColor: "rgba(42, 33, 24, 0.08)",
            padding: "2px 5px",
            borderRadius: "4px",
            fontSize: "0.9em",
          }}
        >
          {match[4]}
        </code>
      );
    }

    remaining = remaining.slice(index + match[0].length);
  }

  return parts;
}

export default function FormattedAnswer({ text, streaming = false }) {
  if (!text) return null;

  const cleaned = cleanLatex(text);
  const lines = cleaned.split("\n");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return <div key={idx} style={{ height: "4px" }} />;
        }

        // Check for bullet list item
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          return (
            <div key={idx} style={{ display: "flex", gap: "8px", alignItems: "flex-start", marginLeft: "6px" }}>
              <span style={{ color: "var(--sun-dark)", fontWeight: "bold", fontSize: "14px", lineHeight: "1.4" }}>•</span>
              <span style={{ flex: 1, lineHeight: "1.55" }}>{parseInline(trimmed.slice(2))}</span>
            </div>
          );
        }

        // Check for numbered list item
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
        if (numMatch) {
          return (
            <div key={idx} style={{ display: "flex", gap: "8px", alignItems: "flex-start", marginLeft: "6px" }}>
              <span className="font-mono" style={{ color: "var(--sun-dark)", fontWeight: "bold", fontSize: "13px", lineHeight: "1.55" }}>
                {numMatch[1]}.
              </span>
              <span style={{ flex: 1, lineHeight: "1.55" }}>{parseInline(numMatch[2])}</span>
            </div>
          );
        }

        return (
          <p key={idx} style={{ margin: 0, lineHeight: "1.6" }}>
            {parseInline(line)}
          </p>
        );
      })}
    </div>
  );
}
