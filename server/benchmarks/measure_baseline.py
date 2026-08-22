import os
import sys
import time
import json
import psutil

# Fix Windows stdout encoding for UTF-8 characters (e.g. Hindi)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure server root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.deps import (
    get_embedder,
    get_reranker,
    get_dense_matrix,
    get_corpus_chunks,
    get_bm25s_retriever,
    get_qdrant_client,
)
from app.pipeline.orchestrator import run

def get_process_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def measure():
    initial_rss = get_process_memory_mb()
    print(f"[MEASURE] Initial RSS: {initial_rss:.2f} MB")

    t0 = time.perf_counter()
    embedder = get_embedder()
    t_emb = (time.perf_counter() - t0) * 1000
    rss_emb = get_process_memory_mb()
    print(f"[MEASURE] Embedder loaded: +{rss_emb - initial_rss:.2f} MB (Total: {rss_emb:.2f} MB) in {t_emb:.2f}ms")

    t0 = time.perf_counter()
    reranker = get_reranker()
    t_rerank = (time.perf_counter() - t0) * 1000
    rss_rerank = get_process_memory_mb()
    print(f"[MEASURE] Reranker loaded: +{rss_rerank - rss_emb:.2f} MB (Total: {rss_rerank:.2f} MB) in {t_rerank:.2f}ms")

    t0 = time.perf_counter()
    dense_matrix = get_dense_matrix()
    t_dense = (time.perf_counter() - t0) * 1000
    rss_dense = get_process_memory_mb()
    print(f"[MEASURE] Dense Matrix loaded (mmap): +{rss_dense - rss_rerank:.2f} MB (Total: {rss_dense:.2f} MB) in {t_dense:.2f}ms")

    t0 = time.perf_counter()
    bm25s_retriever = get_bm25s_retriever()
    t_bm25s = (time.perf_counter() - t0) * 1000
    rss_bm25s = get_process_memory_mb()
    print(f"[MEASURE] BM25s Retriever loaded: +{rss_bm25s - rss_dense:.2f} MB (Total: {rss_bm25s:.2f} MB) in {t_bm25s:.2f}ms")

    t0 = time.perf_counter()
    corpus_chunks = get_corpus_chunks()
    t_corpus = (time.perf_counter() - t0) * 1000
    rss_corpus = get_process_memory_mb()
    num_chunks = len(corpus_chunks) if corpus_chunks else 0
    print(f"[MEASURE] Corpus Chunks loaded ({num_chunks} items, shared with BM25s): +{rss_corpus - rss_bm25s:.2f} MB (Total: {rss_corpus:.2f} MB) in {t_corpus:.2f}ms")

    startup_rss = get_process_memory_mb()
    print(f"\n[MEASURE] ACTUAL OPTIMIZED STARTUP RSS: {startup_rss:.2f} MB\n")

    queries = [
        "Who directed the movie Goa?",
        "Who produced the movie Goa?",
        "Goa film music director details",
        "गोआ फिल्म के निर्देशक कौन हैं?",
        "What is the release date and cast of the movie Goa?"
    ]

    latencies = []
    results_summary = []

    for i, q in enumerate(queries, 1):
        t_start = time.perf_counter()
        res = run(query_text=q)
        t_end = time.perf_counter()

        elapsed_ms = (t_end - t_start) * 1000
        latencies.append(elapsed_ms)
        curr_rss = get_process_memory_mb()

        sources = res.sources if hasattr(res, "sources") else []
        top_src = sources[0] if sources else None
        
        results_summary.append({
            "query": q,
            "latency_ms": round(elapsed_ms, 2),
            "rss_mb": round(curr_rss, 2),
            "answer_preview": (res.answer or "")[:80],
            "top_chunk_id": top_src.chunk_id if top_src else "N/A",
            "top_rerank_score": top_src.rerank_score if top_src else None,
            "timings_ms": getattr(res, "timings_ms", {})
        })

        print(f"Query {i}: '{q}'")
        print(f"  -> Latency: {elapsed_ms:.2f} ms | RSS: {curr_rss:.2f} MB | Timings: {getattr(res, 'timings_ms', {})}")
        print(f"  -> Answer: {(res.answer or '')[:60]}...\n")

    avg_latency = sum(latencies) / len(latencies)
    peak_rss = get_process_memory_mb()

    report = {
        "initial_rss_mb": round(initial_rss, 2),
        "startup_rss_mb": round(startup_rss, 2),
        "post_query_rss_mb": round(peak_rss, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "latencies_ms": [round(l, 2) for l in latencies],
        "query_results": results_summary
    }

    print("="*60)
    print(f"OPTIMIZED MEASUREMENT COMPLETE:")
    print(f"  Startup RSS:         {report['startup_rss_mb']} MB")
    print(f"  Post-Query Peak RSS: {report['post_query_rss_mb']} MB")
    print(f"  Average Latency:     {report['avg_latency_ms']} ms")
    print("="*60)

    with open(os.path.join(os.path.dirname(__file__), "optimized_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    measure()
