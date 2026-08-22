import os
import sys
import time
import psutil
import numpy as np
import torch
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core import config
from app.deps import get_embedder, get_dense_matrix
from sentence_transformers import SentenceTransformer
from test_exp2_onnx_embedder import ONNXSentenceTransformer

def run_exp2_int8():
    print("==================================================")
    print("EXPERIMENT 2B: ONNX INT8 Quantization Benchmark")
    print("==================================================")

    models_dir = os.path.join(os.path.dirname(__file__), "..", "data", "models")
    onnx_fp32_path = os.path.join(models_dir, "embedder_fp32.onnx")
    onnx_int8_path = os.path.join(models_dir, "embedder_int8.onnx")

    if not os.path.exists(onnx_int8_path):
        print("Quantizing ONNX FP32 model to INT8 dynamic...")
        quantize_dynamic(
            onnx_fp32_path,
            onnx_int8_path,
            weight_type=QuantType.QUInt8
        )
        print(f"INT8 Model created: {onnx_int8_path} (Size: {os.path.getsize(onnx_int8_path)/(1024*1024):.2f} MB)")

    st_model = SentenceTransformer(config.EMBED_MODEL_NAME)
    st_model.eval()
    tokenizer = st_model.tokenizer

    onnx_fp32 = ONNXSentenceTransformer(onnx_fp32_path, tokenizer)
    onnx_int8 = ONNXSentenceTransformer(onnx_int8_path, tokenizer)

    test_queries = [
        "Who directed the movie Goa?",
        "Who produced the movie Goa?",
        "Goa film music director details",
        "गोआ फिल्म के निर्देशक कौन हैं?",
        "What is the release date and cast of the movie Goa?"
    ]

    dense_matrix = get_dense_matrix()

    print("\n--- Benchmarking Vector & Retrieval Equivalence (INT8 vs PyTorch/FP32) ---")
    int8_matches = True
    cos_sims = []
    latencies_int8 = []

    for q in test_queries:
        with torch.inference_mode():
            vec_pt = st_model.encode(q, normalize_embeddings=True)

        t0 = time.perf_counter()
        vec_int8 = onnx_int8.encode(q, normalize_embeddings=True)
        t_int8 = (time.perf_counter() - t0) * 1000
        latencies_int8.append(t_int8)

        cos_sim = float(np.dot(vec_pt, vec_int8))
        cos_sims.append(cos_sim)

        scores_pt = dense_matrix @ vec_pt
        top_pt = np.argpartition(scores_pt, -10)[-10:]
        top_pt = top_pt[np.argsort(-scores_pt[top_pt])].tolist()

        scores_int8 = dense_matrix @ vec_int8
        top_int8 = np.argpartition(scores_int8, -10)[-10:]
        top_int8 = top_int8[np.argsort(-scores_int8[top_int8])].tolist()

        is_top_match = (top_pt == top_int8)
        if not is_top_match:
            int8_matches = False
            print(f"⚠️ INT8 Discrepancy for query '{q}': Cosine Sim = {cos_sim:.6f}")
            print(f"   PyTorch Top-3: {top_pt[:3]}")
            print(f"   INT8 Top-3:    {top_int8[:3]}")
        else:
            print(f"✓ Query '{q}': Cosine Sim = {cos_sim:.6f} | Top-10 Retrieval Equivalence 100% PERFECT MATCH!")

    avg_int8 = sum(latencies_int8) / len(latencies_int8)

    print("\n--------------------------------------------------")
    print(f"ONNX INT8 Avg Encode Latency: {avg_int8:.2f} ms")
    print(f"Average Cosine Similarity:    {sum(cos_sims)/len(cos_sims):.6f}")
    print(f"INT8 Top-10 Retrieval Match:  {'PASS' if int8_matches else 'FAIL'}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_exp2_int8()
