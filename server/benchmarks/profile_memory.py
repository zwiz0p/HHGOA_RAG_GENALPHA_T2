import os
import sys
import time
import gc
import json
import psutil

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def get_mem():
    p = psutil.Process(os.getpid())
    info = p.memory_info()
    # On Windows: rss is Working Set, private is Private Bytes (USS equivalent)
    private = getattr(info, "private", getattr(info, "pagefile", info.rss))
    return info.rss / (1024 * 1024), private / (1024 * 1024)

def profile():
    steps = []

    def snap(name):
        gc.collect()
        rss, priv = get_mem()
        prev_rss = steps[-1]["rss_mb"] if steps else 0
        prev_priv = steps[-1]["priv_mb"] if steps else 0
        diff_rss = rss - prev_rss
        diff_priv = priv - prev_priv
        step_data = {
            "component": name,
            "rss_mb": round(rss, 2),
            "priv_mb": round(priv, 2),
            "diff_rss_mb": round(diff_rss, 2),
            "diff_priv_mb": round(diff_priv, 2)
        }
        steps.append(step_data)
        print(f"[{name:<40}] RSS: {rss:7.2f} MB (+{diff_rss:6.2f} MB) | Private: {priv:7.2f} MB (+{diff_priv:6.2f} MB)")

    # 1. Base Python
    snap("1. Python Base Interpreter")

    # 2. Basic standard libs & numpy
    import numpy as np
    snap("2. import numpy")

    # 3. FastAPI & Uvicorn
    import fastapi
    import uvicorn
    import pydantic
    snap("3. import fastapi / uvicorn / pydantic")

    # 4. PyTorch
    import torch
    snap("4. import torch (PyTorch C++ Engine)")

    # 5. sentence_transformers
    from sentence_transformers import SentenceTransformer, CrossEncoder
    snap("5. import sentence_transformers")

    # 6. transformers (HuggingFace AutoTokenizer)
    from transformers import AutoTokenizer
    snap("6. import transformers (AutoTokenizer)")

    # 7. ONNX Runtime
    import onnxruntime as ort
    snap("7. import onnxruntime")

    # 8. BM25s library
    import bm25s
    snap("8. import bm25s")

    # 9. Load ONNX Embedder Session
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from app.core import config

    onnx_embedder_path = os.path.join(config.BASE_DIR, "data", "models", "embedder_fp32.onnx")
    if os.path.exists(onnx_embedder_path):
        sess_emb = ort.InferenceSession(onnx_embedder_path, providers=["CPUExecutionProvider"])
        tok_emb = AutoTokenizer.from_pretrained(config.EMBED_MODEL_NAME)
        snap("9. Load ONNX Embedder Session + Tokenizer")

    # 10. Load ONNX Reranker Session
    onnx_reranker_path = os.path.join(config.BASE_DIR, "data", "models", "reranker_fp32.onnx")
    if os.path.exists(onnx_reranker_path):
        sess_rerank = ort.InferenceSession(onnx_reranker_path, providers=["CPUExecutionProvider"])
        tok_rerank = AutoTokenizer.from_pretrained(config.RERANK_MODEL_NAME)
        snap("10. Load ONNX Reranker Session + Tokenizer")

    # 11. Memory-Mapped Dense Matrix
    dense_matrix = np.load(config.DENSE_VECTORS_PATH, mmap_mode="r")
    snap("11. Load dense_vectors.npy (mmap_mode='r')")

    # 12. BM25s Index (load_corpus=False)
    bm25s_retriever = bm25s.BM25.load(config.BM25S_INDEX_DIR, load_corpus=False)
    snap("12. Load BM25s Index (load_corpus=False)")

    # 13. Corpus Chunks
    from app.deps import get_corpus_chunks
    chunks = get_corpus_chunks()
    snap("13. Load Corpus Chunks (chunks_sentence_aware.jsonl)")

    # 14. PyTorch SentenceTransformer (if also instantiated)
    pt_embedder = SentenceTransformer(config.EMBED_MODEL_NAME)
    pt_embedder.eval()
    snap("14. Instantiate PyTorch SentenceTransformer (Parallel Test)")

    # 15. PyTorch CrossEncoder (if also instantiated)
    pt_reranker = CrossEncoder(config.RERANK_MODEL_NAME)
    pt_reranker.model.eval()
    snap("15. Instantiate PyTorch CrossEncoder (Parallel Test)")

    # Check imported modules
    modules = list(sys.modules.keys())
    has_torch = "torch" in sys.modules
    has_st = "sentence_transformers" in sys.modules

    print("\n==================================================")
    print("IMPORT GRAPH AUDIT:")
    print(f"  PyTorch ('torch') imported in sys.modules:              {has_torch}")
    print(f"  SentenceTransformers ('sentence_transformers') imported: {has_st}")
    print(f"  Total loaded modules in sys.modules:                   {len(modules)}")
    print("==================================================")

    with open(os.path.join(os.path.dirname(__file__), "memory_profile_report.json"), "w", encoding="utf-8") as f:
        json.dump({
            "steps": steps,
            "has_torch_imported": has_torch,
            "has_sentence_transformers_imported": has_st,
            "total_modules": len(modules)
        }, f, indent=2)

if __name__ == "__main__":
    profile()
