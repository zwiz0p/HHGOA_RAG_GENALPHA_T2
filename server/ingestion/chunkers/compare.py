"""
Runs all chunking strategies over the same document set and reports
comparative stats (chunk count, avg/median/max token size, std dev, boundary clipping).

Generates the metrics required for docs/CHUNKING_COMPARISON.md.

Usage:
    python -m ingestion.chunkers.compare --docs data/raw/documents_hi_8000.jsonl --sample 1000
"""

import argparse
import json
import re
import statistics as stats

from . import fixed_overlap, sentence_aware, metadata_aware

PUNCTUATION_END = re.compile(r"[.!?।]$")


def load_docs(path):
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs


def naive_fixed_size_chunk(doc, chunk_size=100):
    tokens = doc["text"].split()
    if len(tokens) <= chunk_size:
        return [{"text": doc["text"], "chunk_id": f"{doc['doc_id']}_naive_0", "chunk_strategy": "fixed_size", "doc_id": doc["doc_id"]}]
    chunks = []
    for i in range(0, len(tokens), chunk_size):
        window = tokens[i:i + chunk_size]
        chunks.append({
            "text": " ".join(window),
            "chunk_id": f"{doc['doc_id']}_naive_{i//chunk_size}",
            "chunk_strategy": "fixed_size",
            "doc_id": doc["doc_id"],
        })
    return chunks


def summarize(chunks, label):
    sizes = [c.get("token_count", len(c["text"].split())) for c in chunks]
    if not sizes:
        print(f"{label}: no chunks produced")
        return {}

    # Calculate boundary preservation rate: percentage of chunks that end with valid sentence punctuation
    preserved_boundaries = sum(1 for c in chunks if PUNCTUATION_END.search(c["text"].strip()))
    boundary_preservation_pct = (preserved_boundaries / len(chunks)) * 100.0

    res = {
        "label": label,
        "chunk_count": len(chunks),
        "avg_tokens": stats.mean(sizes),
        "median_tokens": stats.median(sizes),
        "max_tokens": max(sizes),
        "min_tokens": min(sizes),
        "stdev_tokens": stats.pstdev(sizes),
        "boundary_preservation_pct": boundary_preservation_pct,
    }

    print(f"\n--- {label} ---")
    print(f"chunk_count               : {res['chunk_count']}")
    print(f"avg_tokens                : {res['avg_tokens']:.1f}")
    print(f"median_tokens             : {res['median_tokens']:.1f}")
    print(f"max_tokens                : {res['max_tokens']}")
    print(f"min_tokens                : {res['min_tokens']}")
    print(f"stdev_tokens              : {res['stdev_tokens']:.1f}")
    print(f"boundary_preservation_rate: {res['boundary_preservation_pct']:.1f}%")
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", required=True)
    parser.add_argument("--sample", type=int, default=1000, help="cap docs for speed")
    args = parser.parse_args()

    docs = load_docs(args.docs)[: args.sample]
    print(f"Comparing chunking strategies over {len(docs)} documents...")

    naive_chunks = []
    fixed_chunks = []
    sentence_chunks = []
    meta_chunks = []

    for doc in docs:
        naive_chunks += naive_fixed_size_chunk(doc, chunk_size=100)
        fixed_chunks += fixed_overlap.chunk_document(doc, chunk_size=120, overlap=30)
        sentence_chunks += sentence_aware.chunk_document(doc, target_tokens=100)
        meta_chunks += metadata_aware.chunk_document_with(sentence_aware.chunk_document, doc, target_tokens=100)

    summarize(naive_chunks, "fixed_size (chunk_size=100, overlap=0)")
    summarize(fixed_chunks, "fixed_overlap (chunk_size=120, overlap=30)")
    summarize(sentence_chunks, "sentence_aware (target_tokens=100)")
    summarize(meta_chunks, "metadata_aware (sentence_aware + metadata tags)")


if __name__ == "__main__":
    main()

