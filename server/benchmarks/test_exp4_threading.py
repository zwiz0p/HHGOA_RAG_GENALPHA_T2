import os
import sys
import time
import psutil
import torch
import onnxruntime as ort

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core import config
from app.deps import get_embedder, get_reranker

def run_exp4():
    print("==================================================")
    print("EXPERIMENT 4: OMP/MKL/Torch Thread Allocation Benchmark")
    print("==================================================")

    embedder = get_embedder()
    reranker = get_reranker()

    test_queries = [
        "Who directed the movie Goa?",
        "Who produced the movie Goa?",
        "Goa film music director details",
        "गोआ फिल्म के निर्देशक कौन हैं?",
        "What is the release date and cast of the movie Goa?"
    ]

    for threads in [1, 2, 4]:
        torch.set_num_threads(threads)
        
        latencies = []
        for q in test_queries:
            t0 = time.perf_counter()
            with torch.inference_mode():
                v = embedder.encode(q, normalize_embeddings=True)
            elapsed = (time.perf_counter() - t0) * 1000
            latencies.append(elapsed)

        avg_lat = sum(latencies) / len(latencies)
        print(f"Torch Num Threads = {threads}: Avg Encode Latency = {avg_lat:.2f} ms")

    print("==================================================")

if __name__ == "__main__":
    run_exp4()
