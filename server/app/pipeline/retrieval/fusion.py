"""
Reciprocal Rank Fusion (RRF) — merges dense and BM25 candidate lists into
one ranked list without needing their raw scores to be on the same scale
(cosine similarity vs. BM25 score are not comparable directly, RRF sidesteps
that by fusing on RANK instead of score).
"""

from typing import List, Dict

from app.core import config

RRF_K = 60  # standard RRF damping constant


def reciprocal_rank_fusion(dense_results: List[Dict], bm25_results: List[Dict], top_k: int = config.FUSION_TOP_K) -> List[Dict]:
    scores: Dict[str, float] = {}
    payloads: Dict[str, Dict] = {}

    for rank, item in enumerate(dense_results):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        payloads[cid] = item

    for rank, item in enumerate(bm25_results):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        if cid not in payloads:
            payloads[cid] = item

    ranked_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)[:top_k]

    fused = []
    for cid in ranked_ids:
        item = dict(payloads[cid])
        item["fusion_score"] = scores[cid]
        fused.append(item)

    return fused
