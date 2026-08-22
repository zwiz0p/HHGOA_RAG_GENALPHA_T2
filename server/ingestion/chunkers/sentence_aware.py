"""
Strategy 2 — Sentence-aware chunking.

Splits on sentence boundaries (regex-based, language-agnostic punctuation
set to also handle Indic scripts like Devanagari '।'), then greedily groups
consecutive sentences until a target token budget is hit. Never splits
mid-sentence, which fixed-size chunking can do.
"""

import re
from typing import List, Dict

SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?।])\s+")


def split_sentences(text: str) -> List[str]:
    sentences = SENTENCE_BOUNDARY.split(text.strip())
    return [s for s in sentences if s.strip()]


def chunk(text: str, target_tokens: int = 100) -> List[str]:
    sentences = split_sentences(text)
    if not sentences:
        return [text]

    chunks = []
    current: List[str] = []
    current_len = 0

    for sent in sentences:
        sent_len = len(sent.split())
        if current and current_len + sent_len > target_tokens:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
        current.append(sent)
        current_len += sent_len

    if current:
        chunks.append(" ".join(current))

    return chunks


def chunk_document(doc: Dict, target_tokens: int = 100) -> List[Dict]:
    pieces = chunk(doc["text"], target_tokens)
    out = []
    for i, piece in enumerate(pieces):
        c = dict(doc)
        c["text"] = piece
        c["chunk_id"] = f"{doc['doc_id']}_sent_{i}"
        c["chunk_strategy"] = "sentence_aware"
        c["chunk_position"] = i
        out.append(c)
    return out
