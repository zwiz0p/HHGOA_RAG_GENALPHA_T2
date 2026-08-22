"""
Builds a fast C/NumPy bm25s index from processed chunks.
Takes ~5-10 seconds for 160,000 chunks.

Usage:
    python -m ingestion.build_bm25s
"""

import json
import os
import time
import bm25s

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHUNKS_PATH = os.path.join(BASE_DIR, "data", "processed", "chunks_sentence_aware.jsonl")
BM25S_OUT_DIR = os.path.join(BASE_DIR, "data", "processed", "bm25s_index")


def load_chunks(path: str):
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def build_bm25s_index():
    print(f"Loading chunks from {CHUNKS_PATH}...")
    start_t = time.perf_counter()
    chunks = load_chunks(CHUNKS_PATH)
    print(f"Loaded {len(chunks)} chunks in {time.perf_counter() - start_t:.2f}s")

    corpus_texts = [c.get("text", "") for c in chunks]

    print("Tokenizing corpus with bm25s...")
    tok_start = time.perf_counter()
    corpus_tokens = bm25s.tokenize(corpus_texts)
    print(f"Tokenized in {time.perf_counter() - tok_start:.2f}s")

    print("Building BM25 index...")
    idx_start = time.perf_counter()
    retriever = bm25s.BM25(corpus=chunks)
    retriever.index(corpus_tokens)
    print(f"Indexed in {time.perf_counter() - idx_start:.2f}s")

    print(f"Saving bm25s index to {BM25S_OUT_DIR}...")
    os.makedirs(BM25S_OUT_DIR, exist_ok=True)
    retriever.save(BM25S_OUT_DIR, corpus=chunks)
    print(f"Done! Total time: {time.perf_counter() - start_t:.2f}s")


if __name__ == "__main__":
    build_bm25s_index()
