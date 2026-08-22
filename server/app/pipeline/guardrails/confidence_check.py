from typing import List, Dict, Tuple
import math

from app.core import config


def check(reranked_candidates: List[Dict]) -> Tuple[bool, float]:
    """
    Evaluates retrieval relevance and domain confidence.
    Returns (passes_confidence_check, confidence_score).
    """
    if not reranked_candidates:
        return False, 0.0

    top_score = reranked_candidates[0].get("rerank_score", 0.0)

    # If score is from heuristic reranker (already normalized 0..1)
    if 0.0 <= top_score <= 1.0:
        confidence = float(top_score)
        passes = confidence >= 0.42
        return passes, round(confidence, 4)

    # If unbounded cross-encoder score, squash with sigmoid
    normalized = 1.0 / (1.0 + math.exp(-top_score))
    passes = normalized >= config.MIN_RETRIEVAL_SCORE
    return passes, round(normalized, 4)
