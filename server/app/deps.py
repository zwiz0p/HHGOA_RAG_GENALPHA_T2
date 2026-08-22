import json
import os
import pickle
from functools import lru_cache
from typing import Optional, List, Dict

import numpy as np
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from qdrant_client import QdrantClient
import bm25s

from app.core import config

# Optimize CPU thread allocation for torch inference
torch.set_num_threads(4)
torch.set_grad_enabled(False)



@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    embedder = SentenceTransformer(config.EMBED_MODEL_NAME)
    embedder.eval()
    return embedder


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    reranker = CrossEncoder(config.RERANK_MODEL_NAME)
    reranker.model.eval()
    return reranker


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
        return bm25s.BM25.load(config.BM25S_INDEX_DIR, load_corpus=True)
    return None


@lru_cache(maxsize=1)
def get_bm25_index():
    if os.path.exists(config.BM25_INDEX_PATH):
        with open(config.BM25_INDEX_PATH, "rb") as f:
            return pickle.load(f)  # fallback {"bm25": BM25Okapi, "chunks": [...]}
    return None


