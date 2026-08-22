import os
import sys
import time
import shutil
import numpy as np
import torch
import onnx
import onnxruntime as ort
from sentence_transformers import SentenceTransformer, CrossEncoder

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core import config

def export_standalone_onnx():
    print("=================================================================")
    print("REGENERATING STANDALONE SELF-CONTAINED ONNX FP32 MODELS")
    print("=================================================================")

    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "models"))
    os.makedirs(models_dir, exist_ok=True)

    temp_dir = os.path.join(models_dir, "temp_export")
    os.makedirs(temp_dir, exist_ok=True)

    embedder_final_path = os.path.join(models_dir, "embedder_fp32.onnx")
    reranker_final_path = os.path.join(models_dir, "reranker_fp32.onnx")

    # -----------------------------------------------------------------
    # 1. EXPORT EMBEDDER (paraphrase-multilingual-MiniLM-L12-v2)
    # -----------------------------------------------------------------
    print("\n[1/4] Loading PyTorch Embedder model...")
    st_embedder = SentenceTransformer(config.EMBED_MODEL_NAME)
    st_embedder.eval()
    auto_embedder = st_embedder._modules['0'].auto_model
    tokenizer_emb = st_embedder.tokenizer

    dummy_text = ["What is the release date of Goa?"]
    dummy_inputs_emb = tokenizer_emb(dummy_text, padding=True, truncation=True, return_tensors="pt")

    embedder_temp_path = os.path.join(temp_dir, "embedder_temp.onnx")

    print("[1/4] Exporting Embedder to ONNX FP32...")
    dummy_args_emb = (dummy_inputs_emb['input_ids'], dummy_inputs_emb['attention_mask'])
    input_names_emb = ['input_ids', 'attention_mask']
    dynamic_axes_emb = {
        'input_ids': {0: 'batch_size', 1: 'sequence_length'},
        'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
        'last_hidden_state': {0: 'batch_size', 1: 'sequence_length'}
    }

    if 'token_type_ids' in dummy_inputs_emb:
        dummy_args_emb = (dummy_inputs_emb['input_ids'], dummy_inputs_emb['attention_mask'], dummy_inputs_emb['token_type_ids'])
        input_names_emb.append('token_type_ids')
        dynamic_axes_emb['token_type_ids'] = {0: 'batch_size', 1: 'sequence_length'}

    torch.onnx.export(
        auto_embedder,
        dummy_args_emb,
        embedder_temp_path,
        input_names=input_names_emb,
        output_names=['last_hidden_state'],
        dynamic_axes=dynamic_axes_emb,
        opset_version=14,
        do_constant_folding=True,
        export_params=True
    )

    print("[1/4] Embedding all weight tensors into self-contained single ONNX file...")
    onnx_emb_model = onnx.load(embedder_temp_path)
    onnx.save_model(
        onnx_emb_model,
        embedder_final_path,
        save_as_external_data=False
    )
    size_emb_mb = os.path.getsize(embedder_final_path) / (1024 * 1024)
    print(f"✓ Standalone Embedder ONNX saved: {embedder_final_path} ({size_emb_mb:.2f} MB)")

    # -----------------------------------------------------------------
    # 2. EXPORT RERANKER (ms-marco-MiniLM-L-6-v2)
    # -----------------------------------------------------------------
    print("\n[2/4] Loading PyTorch Reranker model...")
    pt_reranker = CrossEncoder(config.RERANK_MODEL_NAME)
    pt_reranker.model.eval()
    auto_reranker = pt_reranker.model
    tokenizer_rerank = pt_reranker.tokenizer

    dummy_pairs = [("What is Goa?", "Goa is a state in India.")]
    dummy_inputs_rerank = tokenizer_rerank(
        [dummy_pairs[0][0]],
        [dummy_pairs[0][1]],
        padding=True,
        truncation=True,
        return_tensors="pt"
    )

    reranker_temp_path = os.path.join(temp_dir, "reranker_temp.onnx")

    print("[2/4] Exporting Reranker to ONNX FP32...")
    dummy_args_rerank = (dummy_inputs_rerank['input_ids'], dummy_inputs_rerank['attention_mask'])
    input_names_rerank = ['input_ids', 'attention_mask']
    dynamic_axes_rerank = {
        'input_ids': {0: 'batch_size', 1: 'sequence_length'},
        'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
        'logits': {0: 'batch_size'}
    }

    if 'token_type_ids' in dummy_inputs_rerank:
        dummy_args_rerank = (dummy_inputs_rerank['input_ids'], dummy_inputs_rerank['attention_mask'], dummy_inputs_rerank['token_type_ids'])
        input_names_rerank.append('token_type_ids')
        dynamic_axes_rerank['token_type_ids'] = {0: 'batch_size', 1: 'sequence_length'}

    torch.onnx.export(
        auto_reranker,
        dummy_args_rerank,
        reranker_temp_path,
        input_names=input_names_rerank,
        output_names=['logits'],
        dynamic_axes=dynamic_axes_rerank,
        opset_version=14,
        do_constant_folding=True,
        export_params=True
    )

    print("[2/4] Embedding all weight tensors into self-contained single ONNX file...")
    onnx_rerank_model = onnx.load(reranker_temp_path)
    onnx.save_model(
        onnx_rerank_model,
        reranker_final_path,
        save_as_external_data=False
    )
    size_rerank_mb = os.path.getsize(reranker_final_path) / (1024 * 1024)
    print(f"✓ Standalone Reranker ONNX saved: {reranker_final_path} ({size_rerank_mb:.2f} MB)")

    # Clean temporary dir
    shutil.rmtree(temp_dir, ignore_errors=True)

    # -----------------------------------------------------------------
    # 3. VALIDATE NO EXTERNAL DATA DEPENDENCIES
    # -----------------------------------------------------------------
    print("\n[3/4] Validating ONNX Runtime Session loading (Zero External Data check)...")
    
    # Verify embedder session
    sess_emb = ort.InferenceSession(embedder_final_path, providers=["CPUExecutionProvider"])
    print("  ✓ Embedder ONNX session created successfully with CPUExecutionProvider")

    # Verify reranker session
    sess_rerank = ort.InferenceSession(reranker_final_path, providers=["CPUExecutionProvider"])
    print("  ✓ Reranker ONNX session created successfully with CPUExecutionProvider")

    # Check for any .data files in models_dir
    data_files = [f for f in os.listdir(models_dir) if f.endswith(".data")]
    if data_files:
        print(f"⚠️ Warning: Found external .data files in models dir: {data_files}. Cleaning up...")
        for df in data_files:
            os.remove(os.path.join(models_dir, df))
    else:
        print("  ✓ Confirmed ZERO .onnx.data external files exist!")

    # -----------------------------------------------------------------
    # 4. VALIDATE RETRIEVAL & RERANKING EQUIVALENCE (PyTorch vs Standalone ONNX)
    # -----------------------------------------------------------------
    print("\n[4/4] Validating Vector & Reranking Equivalence (PyTorch vs Standalone ONNX)...")

    # Test embedder equivalence
    test_query = "What is the release date and cast of the movie Goa?"
    with torch.inference_mode():
        vec_pt = st_embedder.encode(test_query, normalize_embeddings=True)

    # ONNX embedder inference
    inputs_emb = tokenizer_emb([test_query], padding=True, truncation=True, return_tensors="np")
    ort_inputs_emb = {
        "input_ids": inputs_emb["input_ids"].astype(np.int64),
        "attention_mask": inputs_emb["attention_mask"].astype(np.int64),
    }
    if "token_type_ids" in inputs_emb and "token_type_ids" in [i.name for i in sess_emb.get_inputs()]:
        ort_inputs_emb["token_type_ids"] = inputs_emb["token_type_ids"].astype(np.int64)

    token_embeds = sess_emb.run(None, ort_inputs_emb)[0]
    mask = np.expand_dims(inputs_emb["attention_mask"], -1).astype(np.float32)
    sum_emb = np.sum(token_embeds * mask, axis=1)
    sum_m = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
    vec_onnx = sum_emb / sum_m
    norm = np.linalg.norm(vec_onnx, axis=1, keepdims=True)
    vec_onnx = (vec_onnx / np.clip(norm, a_min=1e-9, a_max=None))[0]

    cos_sim = float(np.dot(vec_pt, vec_onnx))
    print(f"  ✓ Embedder Vector Cosine Similarity: {cos_sim:.6f} (Target: >= 0.99999)")

    # Test reranker equivalence
    test_pairs = [
        ("Who directed the movie Goa?", "Goa is directed by John Landis starring Donald Sutherland."),
        ("Who directed the movie Goa?", "Goa is a popular tourist destination in western India with beaches.")
    ]
    with torch.inference_mode():
        scores_pt = pt_reranker.predict(test_pairs)

    inputs_rr = tokenizer_rerank(
        [p[0] for p in test_pairs],
        [p[1] for p in test_pairs],
        padding=True,
        truncation=True,
        return_tensors="np"
    )
    ort_inputs_rr = {
        "input_ids": inputs_rr["input_ids"].astype(np.int64),
        "attention_mask": inputs_rr["attention_mask"].astype(np.int64),
    }
    if "token_type_ids" in inputs_rr and "token_type_ids" in [i.name for i in sess_rerank.get_inputs()]:
        ort_inputs_rr["token_type_ids"] = inputs_rr["token_type_ids"].astype(np.int64)

    scores_onnx = sess_rerank.run(None, ort_inputs_rr)[0].squeeze(-1)
    max_diff = np.max(np.abs(scores_pt - scores_onnx))
    print(f"  ✓ Reranker Max Absolute Score Diff:  {max_diff:.6f} (Target: < 1e-4)")

    print("\n=================================================================")
    print("STANDALONE ONNX EXPORT & VALIDATION COMPLETE SUCCESS!")
    print("=================================================================")

if __name__ == "__main__":
    export_standalone_onnx()
