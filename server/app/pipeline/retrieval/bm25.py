from typing import List, Dict
import bm25s

from app.core import config
from app.deps import get_bm25s_retriever, get_bm25_index


def bm25_search(query: str, top_k: int = config.BM25_TOP_K) -> List[Dict]:
    # 1. High-performance bm25s path (<10ms)
    retriever = get_bm25s_retriever()
    if retriever is not None:
        query_tokens = bm25s.tokenize(query, show_progress=False)
        docs, scores = retriever.retrieve(query_tokens, k=top_k, show_progress=False)
        
        results = []
        if len(docs) > 0:
            for doc, score in zip(docs[0], scores[0]):
                payload = dict(doc)
                payload["bm25_score"] = float(score)
                results.append(payload)
        return results

    # 2. Fallback to legacy rank_bm25 pickle if bm25s index directory is not found
    index = get_bm25_index()
    if index is not None:
        bm25 = index["bm25"]
        chunks = index["chunks"]

        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)

        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for i in ranked:
            payload = dict(chunks[i])
            payload["bm25_score"] = float(scores[i])
            results.append(payload)

        return results

    return []


search_bm25 = bm25_search


