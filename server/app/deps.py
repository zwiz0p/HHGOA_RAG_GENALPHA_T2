import json
import os
import pickle
from functools import lru_cache
from typing import Optional, List, Dict

import numpy as np
from qdrant_client import QdrantClient
import bm25s

from app.core import config



import onnxruntime as ort
from transformers import AutoTokenizer

ONNX_MODEL_DIR = os.path.join(config.BASE_DIR, "data", "models")
ONNX_EMBEDDER_PATH = os.path.join(ONNX_MODEL_DIR, "embedder_fp32.onnx")
ONNX_RERANKER_PATH = os.path.join(ONNX_MODEL_DIR, "reranker_fp32.onnx")


class ONNXEmbedderWrapper:
    def __init__(self, onnx_path: str, model_name: str):
        self.session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.input_names = [i.name for i in self.session.get_inputs()]

    def encode(self, sentences, show_progress_bar=False, normalize_embeddings=True):
        is_single = isinstance(sentences, str)
        if is_single:
            sentences = [sentences]

        inputs = self.tokenizer(sentences, padding=True, truncation=True, max_length=512, return_tensors="np")
        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64),
        }
        if "token_type_ids" in inputs and "token_type_ids" in self.input_names:
            ort_inputs["token_type_ids"] = inputs["token_type_ids"].astype(np.int64)

        ort_outputs = self.session.run(None, ort_inputs)
        token_embeddings = ort_outputs[0]
        input_mask = inputs["attention_mask"]

        input_mask_expanded = np.expand_dims(input_mask, -1).astype(np.float32)
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        embeddings = sum_embeddings / sum_mask

        if normalize_embeddings:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.clip(norms, a_min=1e-9, a_max=None)

        return embeddings[0] if is_single else embeddings


class ONNXRerankerWrapper:
    def __init__(self, onnx_path: str, model_name: str):
        self.session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
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
        logits = ort_outputs[0].squeeze(-1)
        return logits


@lru_cache(maxsize=1)
def get_embedder():
    if os.path.exists(ONNX_EMBEDDER_PATH):
        return ONNXEmbedderWrapper(ONNX_EMBEDDER_PATH, config.EMBED_MODEL_NAME)
    from app.legacy_pytorch import get_pytorch_embedder
    return get_pytorch_embedder(config.EMBED_MODEL_NAME)


@lru_cache(maxsize=1)
def get_reranker():
    if os.path.exists(ONNX_RERANKER_PATH):
        return ONNXRerankerWrapper(ONNX_RERANKER_PATH, config.RERANK_MODEL_NAME)
    from app.legacy_pytorch import get_pytorch_reranker
    return get_pytorch_reranker(config.RERANK_MODEL_NAME)


@lru_cache(maxsize=1)
def get_qdrant_client() -> Optional[QdrantClient]:
    try:
        return QdrantClient(path=config.QDRANT_PATH)
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_dense_matrix() -> np.ndarray:
    if os.path.exists(config.DENSE_VECTORS_PATH):
        return np.load(config.DENSE_VECTORS_PATH, mmap_mode="r")
    return None


@lru_cache(maxsize=1)
def get_corpus_chunks():
    retriever = get_bm25s_retriever()
    if retriever is not None and getattr(retriever, "corpus", None) is not None:
        return retriever.corpus

    path = config.CHUNKS_PATH
    if not os.path.exists(path):
        bm25s_corpus = os.path.join(config.BM25S_INDEX_DIR, "corpus.jsonl")
        if os.path.exists(bm25s_corpus):
            path = bm25s_corpus
    if os.path.exists(path):
        chunks = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
        return chunks
    return None


@lru_cache(maxsize=1)
def get_bm25s_retriever():
    if os.path.exists(config.BM25S_INDEX_DIR):
        return bm25s.BM25.load(config.BM25S_INDEX_DIR, load_corpus=False)
    return None


@lru_cache(maxsize=1)
def get_bm25_index():
    if os.path.exists(config.BM25_INDEX_PATH):
        with open(config.BM25_INDEX_PATH, "rb") as f:
            return pickle.load(f)  # fallback {"bm25": BM25Okapi, "chunks": [...]}
    return None


