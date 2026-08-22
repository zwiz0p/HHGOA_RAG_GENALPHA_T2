"""
Strategy 4 — Metadata-aware wrapping.

Not a competing splitter — a decorator over any of the other three that
enriches each chunk with retrieval-useful metadata, and additionally
computes cheap chunk-level stats (token count, has_digit, is_gold) so the
retriever/reranker can use them as filtering or scoring signals later
(e.g. boost is_selected passages during eval, filter by language, filter
by query_type for numeric vs. descriptive questions).
"""

from typing import List, Dict, Callable
import re

HAS_DIGIT = re.compile(r"\d")


def enrich(chunks: List[Dict]) -> List[Dict]:
    enriched = []
    for c in chunks:
        c = dict(c)
        c["token_count"] = len(c["text"].split())
        c["has_digit"] = bool(HAS_DIGIT.search(c["text"]))
        c["is_gold"] = c.get("is_selected", False)
        enriched.append(c)
    return enriched


def chunk_document_with(base_chunker: Callable[..., List[Dict]], doc: Dict, **kwargs) -> List[Dict]:
    chunks = base_chunker(doc, **kwargs)
    return enrich(chunks)
