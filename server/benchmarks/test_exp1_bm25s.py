import os
import sys
import time
import json
import psutil
import numpy as np

# Fix Windows stdout encoding for UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core import config
from app.deps import (
    get_embedder,
    get_reranker,
    get_dense_matrix,
    get_corpus_chunks,
)
import bm25s
from app.pipeline.orchestrator import run

def get_process_memory_mb():
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

def run_exp1_test():
    print("==================================================")
    print("EXPERIMENT 1: BM25s Corpus Unloading Analysis")
    print("==================================================")

    rss_start = get_process_memory_mb()

    # 1. Test bm25s.BM25.load(..., load_corpus=False)
    t0 = time.perf_counter()
    retriever_no_corpus = bm25s.BM25.load(config.BM25S_INDEX_DIR, load_corpus=False)
    t_no_corpus = (time.perf_counter() - t0) * 1000
    rss_no_corpus = get_process_memory_mb() - rss_start
    print(f"BM25s (load_corpus=False) RAM: +{rss_no_corpus:.2f} MB in {t_no_corpus:.2f}ms")

    # 2. Test bm25s.BM25.load(..., load_corpus=True)
    t0 = time.perf_counter()
    retriever_with_corpus = bm25s.BM25.load(config.BM25S_INDEX_DIR, load_corpus=True)
    t_with_corpus = (time.perf_counter() - t0) * 1000
    rss_with_corpus = get_process_memory_mb() - rss_start - rss_no_corpus
    print(f"BM25s (load_corpus=True) RAM: +{rss_with_corpus:.2f} MB in {t_with_corpus:.2f}ms")

    # 3. Test Retrieval Equivalence across test queries
    queries = [
        "Who directed the movie Goa?",
        "Who produced the movie Goa?",
        "Goa film music director details",
        "गोआ फिल्म के निर्देशक कौन हैं?",
        "What is the release date and cast of the movie Goa?"
    ]

    chunks = get_corpus_chunks()
    
    all_equal = True
    for q in queries:
        tokens = bm25s.tokenize(q, show_progress=False)

        # Retrieve with corpus
        docs_c, scores_c = retriever_with_corpus.retrieve(tokens, k=config.BM25_TOP_K, show_progress=False)
        results_c = []
        if len(docs_c) > 0:
            for d, s in zip(docs_c[0], scores_c[0]):
                p = dict(d)
                p["bm25_score"] = float(s)
                results_c.append(p)

        # Retrieve without corpus (by index)
        indices_nc, scores_nc = retriever_no_corpus.retrieve(tokens, k=config.BM25_TOP_K, show_progress=False)
        results_nc = []
        if len(indices_nc) > 0:
            for idx, s in zip(indices_nc[0], scores_nc[0]):
                p = dict(chunks[idx])
                p["bm25_score"] = float(s)
                results_nc.append(p)

        # Compare equivalence
        ids_c = [r["chunk_id"] for r in results_c]
        ids_nc = [r["chunk_id"] for r in results_nc]
        scores_equal = np.allclose([r["bm25_score"] for r in results_c], [r["bm25_score"] for r in results_nc])

        is_eq = (ids_c == ids_nc) and scores_equal
        if not is_eq:
            all_equal = False
            print(f"❌ Discrepancy for query '{q}':")
            print(f"   Corpus IDs:     {ids_c[:3]}")
            print(f"   No-Corpus IDs:  {ids_nc[:3]}")
        else:
            print(f"✓ Query '{q}': Top-K Retrieval Equivalence 100% PERFECT MATCH!")

    print(f"\nOverall Equivalence Passed: {all_equal}")
    print(f"Memory Saved by load_corpus=False: {rss_with_corpus:.2f} MB")
    print("==================================================")

if __name__ == "__main__":
    run_exp1_test()
