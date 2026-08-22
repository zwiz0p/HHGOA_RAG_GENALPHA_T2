# AURA Architecture — Multilingual Voice RAG & Knowledge Engine

## 1. System Pipeline Overview

```
User Input (Audio Mic Stream / Text Input)
      │
      ▼
Speech-to-Text (Sarvam Saarika v2 — Bilingual Indic ASR)
      │
      ▼
Pre-Retrieval Intent Guardrail & Router (< 0.1 ms)
      ├── Fast-Path Intent / Greeting ───────► Instant Conversational Reply (0.04 ms)
      └── Factual / Search Query
            │
            ▼
┌──────────────────────────────────────────────────────────┐
│             PARALLEL HYBRID RETRIEVAL (~28 ms)           │
│  Dense BLAS Vector Dot-Product (28 ms) ─┐                │
│                                          ├─► RRF Fusion ─► Cross-Encoder Reranker (Top-4, ~40 ms)
│  C-Accelerated BM25s Lexical Search (2 ms) ─┘             │
└──────────────────────────────────────────────────────────┘
            │
            ▼
Confidence Score Guardrail & Grounding Gate (< 0.1 ms)
      │
      ├── High In-Domain Confidence (>= 0.65)
      │     ▼
      │   Context-Constrained Synthesis (Gemini 2.5 Flash)
      │     ▼
      │   Grounding Guardrail (Citation & Containment Verification)
      │     ▼
      │   Badge: [📚 Backed by Knowledge Base]
      │
      └── Out-of-Domain / Low Confidence (< 0.65)
            ▼
          General World Knowledge Synthesis
            ▼
          Badge: [🌐 General Knowledge Mode]
            ▼
          Disclaimer: "Couldn't find this in MSMARCO, answering from general knowledge"
```

---

## 2. Deep Dive: Pipeline Subsystems

### A. Pre-Retrieval Intent Guardrail & Router
- **Latency:** **`< 0.10 ms`**
- **Mechanism:** High-speed compiled regex intent matcher.
- **Roles:**
  - Fast-paths common greetings ("Hello", "Who are you?", "नमस्ते") directly to cached responses, bypassing the retrieval engine entirely.
  - Rejects empty, noisy, or nonsensical input early before consuming compute.

### B. Parallel Hybrid Retrieval Engine
- **Target Latency:** Sub-200ms *(Achieved: **`~65 ms`**)*.
- **Dense Vector Search:**
  - Embeddings generated via `paraphrase-multilingual-MiniLM-L12-v2`.
  - Stored as a contiguous in-memory float32 matrix (`172,364 x 384`).
  - Search executed via BLAS matrix-vector product (`dense_matrix @ query_vec`) with `np.argpartition` selection in **`~28 ms`**.
- **Lexical Search (BM25s):**
  - C-accelerated in-memory BM25s inverted index over 172k passages.
  - Queries tokenized and scored in **`~2 ms`**.
- **Reciprocal Rank Fusion (RRF):**
  - $RRF(d) = \sum_{m \in \{dense, bm25\}} \frac{1}{60 + rank_m(d)}$.
  - Merges dense semantic hits with exact lexical matches in **`0.04 ms`**.
- **Cross-Encoder Neural Reranking:**
  - Evaluates the top-4 fused candidate pairs using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
  - Executed inside `with torch.inference_mode():` and 4 CPU worker threads in **`~40 ms`**.

### C. Dual-Mode Grounding & Fallback Gate
- **Hackathon Requirement #6 Compliance:** Prevents false grounding claims on queries outside the indexed MSMARCO dataset.
- **Mode A (Grounded Knowledge Base):** Answers strictly using extracted passage context and validates overlap against source text.
- **Mode B (General World Knowledge):** When top cross-encoder score is below margin, calls Gemini with a general world knowledge system prompt, attaching a clear UI provenance disclaimer.

---

## 3. Frontend Architecture (AURA Studio)

- **Design Aesthetic:** 1970s Pure Retro-Pop with Neo-Brutalist Pop Cards (`2px solid #14151E`, `3px 3px 0px #14151E`).
- **3D Depth Stacking:**
  - `Layer 0 (z-0)`: Fixed flowing decorative 5-stripe rainbow ribbons.
  - `Layer 1 (z-20)`: Dark slate sky (`#14151E`) with star sparkles, floating boombox & moon, and extruded 70s AURA title.
  - `Layer 2 (z-5)`: Desktop flanking character illustrations (Operator Console and Lab Distilling Apparatus).
  - `Layer 3 (z-20)`: Central conversational chat feed and pinned bottom input bar with real-time SSE streaming.
- **Telemetry Waterfall ("Show the Receipts"):** Collapsible drawer displaying exact millisecond metrics for each stage.
