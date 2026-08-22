import re
from typing import List, Dict, Tuple

from app.core import config
from app.deps import get_embedder
import numpy as np

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on",
    "and", "or", "for", "with", "this", "that", "it", "as", "by", "at",
    "कब", "कहाँ", "कहा", "कैसे", "क्या", "क्यों", "किसने", "किसके", "किस", "कौन",
    "है", "हैं", "था", "थी", "थे", "हुई", "हुआ", "हुए", "होना", "होने",
    "की", "का", "के", "में", "पर", "से", "को", "ने", "और", "या", "एक", "यह", "वह"
}


def _tokenize(text: str) -> set:
    words = re.findall(r"[\w\u0900-\u097F]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def lexical_overlap(answer: str, context: str) -> float:
    a_tokens = _tokenize(answer)
    c_tokens = _tokenize(context)
    if not a_tokens:
        return 1.0
    overlap = a_tokens & c_tokens
    return len(overlap) / len(a_tokens)


def embedding_similarity(answer: str, context: str) -> float:
    embedder = get_embedder()
    vecs = embedder.encode([answer, context])
    denom = np.linalg.norm(vecs[0]) * np.linalg.norm(vecs[1])
    return float(np.dot(vecs[0], vecs[1]) / denom) if denom else 0.0


INSUFFICIENT_PATTERNS = [
    r"context is insufficient",
    r"not mentioned in the (context|sources|text|document)",
    r"cannot be answered from the (provided\s)?context",
    r"(context|document|source|sources|text)\s+(does|do|is)\s+not\s+(contain|mention|have|provide|sufficient)",
    r"not\s+(contain|include|provide)\s+.*(information|instructions|details|context|data)",
    r"insufficient context",
    r"not enough information",
    r"no information (is|was|provided)",
    r"संदर्भ अपर्याप्त है",
    r"दी गई जानकारी.*पर्याप्त नहीं",
    r"संदर्भ में.*नहीं",
    r"जानकारी नहीं मिलती",
    r"जानकारी उपलब्ध नहीं",
]


def check(answer: str, retrieved_chunks: List[Dict]) -> Tuple[bool, float]:
    """Returns (is_grounded, grounding_score)."""
    if not answer or not retrieved_chunks:
        return False, 0.0

    lower_ans = answer.lower()
    for pat in INSUFFICIENT_PATTERNS:
        if re.search(pat, lower_ans, re.IGNORECASE):
            return False, 0.0

    context = " ".join(c.get("text", "") for c in retrieved_chunks)

    # 1. Cheap lexical overlap first
    overlap_score = lexical_overlap(answer, context)
    if overlap_score >= config.MIN_GROUNDING_SCORE:
        return True, overlap_score

    # 2. If overlap is low (e.g. heavy paraphrase), fall back to embedding similarity
    sim_score = embedding_similarity(answer, context)
    return sim_score >= config.MIN_GROUNDING_SCORE, sim_score
