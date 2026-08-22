import React from "react";

const COMMON_STOPWORDS = new Set([
  "the", "and", "for", "with", "this", "that", "from", "what", "when", "where", "which",
  "who", "why", "how", "did", "does", "was", "were", "are", "have", "has", "had",
  "been", "into", "over", "after", "before", "more", "most", "some", "such", "only",
  "का", "की", "के", "में", "पर", "से", "को", "ने", "और", "या", "एक", "यह", "वह",
  "है", "हैं", "था", "थी", "थे", "हुई", "हुआ", "हुए", "होना", "होने", "कर", "करने"
]);

/**
 * Highlights meaningful query terms inside retrieved passage text.
 * Purely presentational - zero changes to ranking/data.
 */
export function highlightQueryTerms(text, query) {
  if (!text || !query) return text;

  // 1. Tokenize query
  const cleanQuery = query.toLowerCase().replace(/[^\w\s\u0900-\u097F]/g, " ");
  const terms = cleanQuery
    .split(/\s+/)
    .filter((w) => w.length >= 3 && !COMMON_STOPWORDS.has(w));

  if (terms.length === 0) return text;

  // 2. Escape regex special characters
  const escapedTerms = terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`(${escapedTerms.join("|")})`, "gi");

  const parts = text.split(regex);

  return parts.map((part, i) => {
    const isMatch = terms.some((t) => t.toLowerCase() === part.toLowerCase());
    if (isMatch) {
      return (
        <mark
          key={i}
          className="bg-[#FFE066] text-[#14151E] px-1 rounded font-semibold"
          style={{
            backgroundColor: "#FFE066",
            color: "#14151E",
            padding: "1px 4px",
            borderRadius: "4px",
            fontWeight: 700,
          }}
        >
          {part}
        </mark>
      );
    }
    return part;
  });
}
