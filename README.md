# AURA — Multilingual Voice RAG & Knowledge Engine

> **1970s Retro-Pop Voice Retrieval-Augmented Generation over MSMARCO-XI with Sub-70ms Parallel Search, Dual-Mode Knowledge Grounding, and Real-Time SSE Streaming.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React + Vite](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61DAFB.svg)](https://vitejs.dev/)
[![Search Latency](https://img.shields.io/badge/Search%20%26%20Rank-~65ms%20(Target%20%3C200ms)-brightgreen.svg)](docs/LATENCY_REPORT.md)
[![Chunking Score](https://img.shields.io/badge/Boundary%20Preservation-94.7%25-success.svg)](docs/CHUNKING_COMPARISON.md)

---

## 🌟 Overview & Architectural Philosophy

**AURA** is a production-grade, bilingual (English & Hindi) Voice RAG application built for the **MSMARCO-XI** corpus. It combines sub-second speech transcription, in-memory C-accelerated lexical and dense vector search, deep cross-encoder neural reranking, multi-stage guardrails, and Gemini 2.5 generative synthesis wrapped in an organic 1970s Pure Retro-Pop interface.

### Key Innovations:
1. **Sub-70ms Parallel Hybrid Retrieval ($P_{50} \sim 65\text{ ms}$):**
   - In-memory float32 normalized matrix multiplication with `np.argpartition` selection.
   - C-accelerated `BM25s` retrieval ($< 3\text{ ms}$).
   - Cross-Encoder top-4 candidate slicing under `torch.inference_mode()` with multi-threaded CPU inference.
2. **Dual-Mode Knowledge Grounding:**
   - In-domain MSMARCO queries answer strictly from retrieved context with hallucination detection.
   - Out-of-dataset queries seamlessly route to **General World Knowledge** with clear UI provenance badges, eliminating false grounding claims.
3. **Sub-Millisecond Intent Routing ($< 0.1\text{ ms}$):**
   - High-throughput regex pre-retrieval routing for greetings and conversational intents.
4. **Multi-Strategy Chunking Comparison:**
   - Live 4-way evaluation modal comparing Fixed Overlap, Sentence-Aware (Default), Semantic, and Metadata-Aware chunking.

---

## 📂 Repository Architecture

```
hhgoa-voice-rag/
├── client/                     # React + Vite 70s Retro-Pop Interface
│   ├── public/assets/retro/    # High-resolution PNG & SVG retro illustrations
│   ├── src/
│   │   ├── components/         # ChatContainer, ChatMessage, BottomInputBar, etc.
│   │   ├── hooks/              # useVoiceCapture (Web Audio API amplitude reactivity)
│   │   ├── lib/api.js          # SSE streaming with AbortController cancellation
│   │   ├── App.jsx             # 3-layer depth architecture & horizon canvas
│   │   └── index.css           # Neo-brutalist pop design system & tokens
├── server/                     # High-Performance FastAPI Backend
│   ├── app/
│   │   ├── core/               # Configuration, logging, credentials
│   │   ├── pipeline/           # STT, Dense, BM25s, Rerank, Guardrails, Orchestrator
│   │   ├── main.py             # FastAPI entrypoint, CORS, SSE endpoints
│   │   └── deps.py             # Pre-warmed model & index singletons
│   ├── benchmarks/             # 50-query latency evaluation suite
│   ├── data/                   # 172k+ indexed passages (raw & processed)
│   └── ingestion/              # 4-way offline chunking & indexing pipelines
└── docs/                       # Technical reports & evaluation docs
    ├── ARCHITECTURE.md         # Full end-to-end pipeline specification
    ├── CHUNKING_COMPARISON.md  # 4-way chunking benchmark & empirical analysis
    ├── GUARDRAILS.md           # 5-stage guardrail safety verification
    └── LATENCY_REPORT.md       # Finalized P50/P70/P100 latency tables
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- Sarvam AI API Key (for Saarika v2 STT)
- Google Gemini API Key (for Generative Synthesis)

---

### 1. Backend Setup

```bash
# Navigate to server directory
cd server

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Open .env and add:
# SARVAM_API_KEY=your_sarvam_key
# LLM_API_KEY=your_gemini_key

# Start the FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at `http://127.0.0.1:8000/docs`.

---

### 2. Frontend Setup

```bash
# Navigate to client directory
cd client

# Install dependencies
npm install

# Start Vite development server
npm run dev -- --host
```
The AURA Studio web interface will be accessible at `http://localhost:5173/`.

---

## 📊 Benchmarks & Documentation Links

- 📖 [Full Architecture Breakdown (`docs/ARCHITECTURE.md`)](docs/ARCHITECTURE.md)
- 🔬 [4-Way Chunking Strategy Analysis (`docs/CHUNKING_COMPARISON.md`)](docs/CHUNKING_COMPARISON.md)
- 🛡️ [Guardrails & Safety Validation (`docs/GUARDRAILS.md`)](docs/GUARDRAILS.md)
- ⚡ [Empirical Latency Report ($P_{50} / P_{70} / P_{100}$) (`docs/LATENCY_REPORT.md`)](docs/LATENCY_REPORT.md)

---

## 🛠️ Testing & Validation

```bash
# Run pytest test suite
cd server
pytest tests/ -v

# Run 50-query latency benchmark
python -m benchmarks.run_latency_bench --n 50 --output ../docs/LATENCY_REPORT.md

# Verify frontend production bundle
cd ../client
npm run build
```
