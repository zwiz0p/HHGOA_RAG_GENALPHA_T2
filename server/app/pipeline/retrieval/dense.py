from typing import List, Dict
import numpy as np
from qdrant_client import models

from app.core import config
from app.deps import get_embedder, get_dense_matrix, get_corpus_chunks, get_qdrant_client


def dense_search(query: str, top_k: int = config.DENSE_TOP_K) -> List[Dict]:
    embedder = get_embedder()
    dense_matrix = get_dense_matrix()
    chunks = get_corpus_chunks()

    # 1. High-speed in-memory vector dot-product search (<30ms on CPU)
    if dense_matrix is not None and chunks is not None:
        query_vec = embedder.encode(
            query,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        scores = dense_matrix @ query_vec
        top_idx = np.argpartition(scores, -top_k)[-top_k:]
        top_idx = top_idx[np.argsort(-scores[top_idx])]

        results = []
        for idx in top_idx:
            payload = dict(chunks[idx])
            payload["dense_score"] = float(scores[idx])
            results.append(payload)

        return results

    # 2. Fallback to local Qdrant client
    client = get_qdrant_client()
    query_vector = embedder.encode(
        query,
        show_progress_bar=False,
        normalize_embeddings=True,
    ).tolist()

    hits = client.query_points(
        collection_name=config.QDRANT_COLLECTION,
        query=query_vector,
        search_params=models.SearchParams(hnsw_ef=64, exact=False),
        limit=top_k,
    ).points

    results = []
    for hit in hits:
        payload = dict(hit.payload)
        payload["dense_score"] = float(hit.score)
        results.append(payload)

    return results


search_dense = dense_search



