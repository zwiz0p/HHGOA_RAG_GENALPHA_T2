import os
import sys
import time
import json
import psutil
import numpy as np
import torch
import onnxruntime as ort

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core import config
from app.deps import get_embedder, get_dense_matrix
from sentence_transformers import SentenceTransformer

def get_process_memory_mb():
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

class ONNXSentenceTransformer:
    def __init__(self, onnx_path, tokenizer):
        self.session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        self.tokenizer = tokenizer
        self.input_names = [i.name for i in self.session.get_inputs()]

    def encode(self, sentences, normalize_embeddings=True):
        if isinstance(sentences, str):
            sentences = [sentences]

        inputs = self.tokenizer(sentences, padding=True, truncation=True, return_tensors="np")
        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64),
        }
        if "token_type_ids" in inputs and "token_type_ids" in self.input_names:
            ort_inputs["token_type_ids"] = inputs["token_type_ids"].astype(np.int64)

        ort_outputs = self.session.run(None, ort_inputs)
        token_embeddings = ort_outputs[0] # (batch_size, seq_len, hidden_dim)
        input_mask = inputs["attention_mask"]

        # Mean Pooling
        input_mask_expanded = np.expand_dims(input_mask, -1).astype(np.float32)
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        embeddings = sum_embeddings / sum_mask

        if normalize_embeddings:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.clip(norms, a_min=1e-9, a_max=None)

        return embeddings[0] if len(sentences) == 1 else embeddings

def run_exp2():
    print("==================================================")
    print("EXPERIMENT 2: ONNX Embedder Export & Equivalence")
    print("==================================================")

    models_dir = os.path.join(os.path.dirname(__file__), "..", "data", "models")
    os.makedirs(models_dir, exist_ok=True)
    onnx_fp32_path = os.path.join(models_dir, "embedder_fp32.onnx")

    # 1. Load PyTorch model
    t0 = time.perf_counter()
    rss_0 = get_process_memory_mb()
    st_model = SentenceTransformer(config.EMBED_MODEL_NAME)
    st_model.eval()
    t_pytorch = (time.perf_counter() - t0) * 1000
    rss_pytorch = get_process_memory_mb() - rss_0
    print(f"PyTorch Model loaded: +{rss_pytorch:.2f} MB in {t_pytorch:.2f}ms")

    tokenizer = st_model.tokenizer

    # 2. Test ONNX FP32 Memory & Performance
    onnx_embedder = ONNXSentenceTransformer(onnx_fp32_path, tokenizer)

    test_queries = [
        "Who directed the movie Goa?",
        "Who produced the movie Goa?",
        "Goa film music director details",
        "गोआ फिल्म के निर्देशक कौन हैं?",
        "What is the release date and cast of the movie Goa?"
    ]

    dense_matrix = get_dense_matrix()

    print("\n--- Benchmarking Vector & Retrieval Equivalence ---")
    fp32_matches = True
    cos_sims = []
    latencies_pt = []
    latencies_onnx = []

    for q in test_queries:
        # PyTorch
        t0 = time.perf_counter()
        with torch.inference_mode():
            vec_pt = st_model.encode(q, normalize_embeddings=True)
        t_pt = (time.perf_counter() - t0) * 1000
        latencies_pt.append(t_pt)

        # ONNX FP32
        t0 = time.perf_counter()
        vec_onnx = onnx_embedder.encode(q, normalize_embeddings=True)
        t_onnx = (time.perf_counter() - t0) * 1000
        latencies_onnx.append(t_onnx)

        # Cosine similarity between vectors
        cos_sim = float(np.dot(vec_pt, vec_onnx))
        cos_sims.append(cos_sim)

        # Top-10 Retrieval index matching on dense_matrix
        scores_pt = dense_matrix @ vec_pt
        top_pt = np.argpartition(scores_pt, -10)[-10:]
        top_pt = top_pt[np.argsort(-scores_pt[top_pt])].tolist()

        scores_onnx = dense_matrix @ vec_onnx
        top_onnx = np.argpartition(scores_onnx, -10)[-10:]
        top_onnx = top_onnx[np.argsort(-scores_onnx[top_onnx])].tolist()

        is_top_match = (top_pt == top_onnx)
        if not is_top_match:
            fp32_matches = False
            print(f"❌ Discrepancy for query '{q}': Cosine Sim = {cos_sim:.6f}")
            print(f"   PyTorch Top-3: {top_pt[:3]}")
            print(f"   ONNX FP32 Top-3: {top_onnx[:3]}")
        else:
            print(f"✓ Query '{q}': Cosine Sim = {cos_sim:.6f} | Top-10 Retrieval Equivalence 100% PERFECT MATCH!")

    avg_pt = sum(latencies_pt) / len(latencies_pt)
    avg_onnx = sum(latencies_onnx) / len(latencies_onnx)

    print("\n--------------------------------------------------")
    print(f"PyTorch Avg Encode Latency:   {avg_pt:.2f} ms")
    print(f"ONNX FP32 Avg Encode Latency: {avg_onnx:.2f} ms")
    print(f"Average Cosine Similarity:    {sum(cos_sims)/len(cos_sims):.6f}")
    print(f"Overall Retrieval Equivalence: {'PASS' if fp32_matches else 'FAIL'}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_exp2()
