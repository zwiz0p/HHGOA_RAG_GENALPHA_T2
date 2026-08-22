import os
import sys
import time
import psutil
import numpy as np
import torch
import onnxruntime as ort

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core import config
from app.deps import get_reranker
from sentence_transformers import CrossEncoder

def get_process_memory_mb():
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

class ONNXCrossEncoder:
    def __init__(self, onnx_path, tokenizer):
        self.session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        self.tokenizer = tokenizer
        self.input_names = [i.name for i in self.session.get_inputs()]

    def predict(self, pairs, batch_size=4, show_progress_bar=False):
        queries = [p[0] for p in pairs]
        passages = [p[1] for p in pairs]

        inputs = self.tokenizer(
            queries,
            passages,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np"
        )

        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64),
        }
        if "token_type_ids" in inputs and "token_type_ids" in self.input_names:
            ort_inputs["token_type_ids"] = inputs["token_type_ids"].astype(np.int64)

        ort_outputs = self.session.run(None, ort_inputs)
        logits = ort_outputs[0]
        # CrossEncoder logits to scores (single output unit)
        scores = logits.squeeze(-1)
        return scores

def run_exp3():
    print("==================================================")
    print("EXPERIMENT 3: ONNX CrossEncoder Reranker Export & Benchmark")
    print("==================================================")

    models_dir = os.path.join(os.path.dirname(__file__), "..", "data", "models")
    os.makedirs(models_dir, exist_ok=True)
    onnx_reranker_path = os.path.join(models_dir, "reranker_fp32.onnx")

    # 1. PyTorch Reranker
    t0 = time.perf_counter()
    rss_0 = get_process_memory_mb()
    pt_reranker = CrossEncoder(config.RERANK_MODEL_NAME)
    pt_reranker.model.eval()
    t_pt = (time.perf_counter() - t0) * 1000
    rss_pt = get_process_memory_mb() - rss_0
    print(f"PyTorch Reranker loaded: +{rss_pt:.2f} MB in {t_pt:.2f}ms")

    # 2. Export to ONNX FP32 if needed
    if not os.path.exists(onnx_reranker_path):
        print("Exporting PyTorch CrossEncoder to ONNX FP32...")
        auto_model = pt_reranker.model
        tokenizer = pt_reranker.tokenizer

        dummy_pairs = [("What is Goa?", "Goa is a state in India.")]
        dummy_inputs = tokenizer(
            [dummy_pairs[0][0]],
            [dummy_pairs[0][1]],
            padding=True,
            truncation=True,
            return_tensors="pt"
        )

        dynamic_axes = {
            'input_ids': {0: 'batch_size', 1: 'sequence_length'},
            'attention_mask': {0: 'batch_size', 1: 'sequence_length'}
        }
        input_names = ['input_ids', 'attention_mask']
        dummy_args = (dummy_inputs['input_ids'], dummy_inputs['attention_mask'])

        if 'token_type_ids' in dummy_inputs:
            dummy_args = (dummy_inputs['input_ids'], dummy_inputs['attention_mask'], dummy_inputs['token_type_ids'])
            input_names.append('token_type_ids')
            dynamic_axes['token_type_ids'] = {0: 'batch_size', 1: 'sequence_length'}

        torch.onnx.export(
            auto_model,
            dummy_args,
            onnx_reranker_path,
            input_names=input_names,
            output_names=['logits'],
            dynamic_axes=dynamic_axes,
            opset_version=14
        )
        print(f"ONNX Reranker saved to {onnx_reranker_path} (Size: {os.path.getsize(onnx_reranker_path)/(1024*1024):.2f} MB)")

    # 3. Test ONNX Reranker
    tokenizer = pt_reranker.tokenizer
    onnx_reranker = ONNXCrossEncoder(onnx_reranker_path, tokenizer)

    test_pairs = [
        ("Who directed the movie Goa?", "Goa is directed by John Landis starring Donald Sutherland."),
        ("Who directed the movie Goa?", "Goa is a popular tourist destination in western India with beaches."),
        ("Who produced the movie Goa?", "The movie was produced by Universal Pictures in 1977."),
        ("What is the release date and cast of the movie Goa?", "The Kentucky Fried Movie release date Aug 10 1977 starring Donald Sutherland.")
    ]

    # PyTorch inference
    t0 = time.perf_counter()
    with torch.inference_mode():
        scores_pt = pt_reranker.predict(test_pairs)
    t_pt_inf = (time.perf_counter() - t0) * 1000

    # ONNX inference
    t0 = time.perf_counter()
    scores_onnx = onnx_reranker.predict(test_pairs)
    t_onnx_inf = (time.perf_counter() - t0) * 1000

    max_diff = np.max(np.abs(scores_pt - scores_onnx))
    scores_match = max_diff < 1e-4

    rank_pt = np.argsort(-scores_pt).tolist()
    rank_onnx = np.argsort(-scores_onnx).tolist()
    rank_match = (rank_pt == rank_onnx)

    print("\n--------------------------------------------------")
    print(f"PyTorch Rerank Latency:   {t_pt_inf:.2f} ms")
    print(f"ONNX FP32 Rerank Latency: {t_onnx_inf:.2f} ms")
    print(f"Max Absolute Score Diff:  {max_diff:.6f}")
    print(f"Ranking Equivalence:     {'PASS' if rank_match else 'FAIL'}")
    print(f"Overall Equivalence:     {'PASS' if scores_match and rank_match else 'FAIL'}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_exp3()
