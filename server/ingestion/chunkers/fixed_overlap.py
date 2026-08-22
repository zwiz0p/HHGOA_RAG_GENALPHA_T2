"""
Strategy 1 — Fixed-size chunking with overlap.

Simplest baseline. Splits on whitespace-token count with a sliding window.
Good for uniform passages; wastes tokens on redundant overlap for short
passages (MSMARCO passages are usually already short, so this strategy
mostly acts as a no-op passthrough here — that's expected and worth noting
in the comparison report).
"""

from typing import List, Dict


def chunk(text: str, chunk_size: int = 120, overlap: int = 30) -> List[str]:
    tokens = text.split()
    if len(tokens) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    step = max(chunk_size - overlap, 1)
    while start < len(tokens):
        window = tokens[start:start + chunk_size]
        chunks.append(" ".join(window))
        if start + chunk_size >= len(tokens):
            break
        start += step

    return chunks


def chunk_document(doc: Dict, chunk_size: int = 120, overlap: int = 30) -> List[Dict]:
    pieces = chunk(doc["text"], chunk_size, overlap)
    out = []
    for i, piece in enumerate(pieces):
        c = dict(doc)
        c["text"] = piece
        c["chunk_id"] = f"{doc['doc_id']}_fixed_{i}"
        c["chunk_strategy"] = "fixed_overlap"
        c["chunk_position"] = i
        out.append(c)
    return out
