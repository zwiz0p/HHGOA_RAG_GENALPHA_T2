"""
Embeds chunks and builds two indexes:
  1. Dense vector index (Qdrant, local mode via qdrant-client)
  2. BM25 keyword index (rank_bm25, persisted as pickle)

Both are read by app/pipeline/retrieval/{dense,bm25}.py at query time.
Nothing in this file runs on the live request path — it's an offline job.

Usage:
    python -m ingestion.embed_and_index \
        --docs data/raw/documents_hi_8000.jsonl \
        --strategy sentence_aware
"""

import argparse
import json
import os
import pickle

import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from rank_bm25 import BM25Okapi

from .chunkers import fixed_overlap, sentence_aware, semantic, metadata_aware

EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "msmarco_xi_chunks"
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

STRATEGY_MAP = {
    "fixed_overlap": lambda doc, embedder: metadata_aware.chunk_document_with(fixed_overlap.chunk_document, doc),
    "sentence_aware": lambda doc, embedder: metadata_aware.chunk_document_with(sentence_aware.chunk_document, doc),
    "semantic": lambda doc, embedder: metadata_aware.chunk_document_with(
        semantic.chunk_document, doc, embedder=embedder
    ),
}


def load_docs(path):
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs


def make_embedder(model: SentenceTransformer):
    def embed(texts):
        return model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embed


def build_chunks(docs, strategy: str, embedder):
    chunker = STRATEGY_MAP[strategy]
    all_chunks = []
    for doc in docs:
        if not doc["text"].strip():
            continue
        all_chunks += chunker(doc, embedder)
    return all_chunks


def build_dense_index(chunks, model: SentenceTransformer, qdrant_path: str):
    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks for dense index...")
    vectors = model.encode(texts, show_progress_bar=True, convert_to_numpy=True, batch_size=64)

    client = QdrantClient(path=qdrant_path)  # local, file-backed — no external service needed
    dim = vectors.shape[1]

    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    points = [
        PointStruct(
            id=i,
            vector=vectors[i].tolist(),
            payload={k: v for k, v in chunks[i].items()},
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Dense index built: {len(points)} points at {qdrant_path}")
    return client


def build_bm25_index(chunks, out_path: str):
    tokenized = [c["text"].lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized)
    with open(out_path, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)
    print(f"BM25 index built: {len(chunks)} chunks at {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", required=True)
    parser.add_argument("--strategy", default="sentence_aware", choices=list(STRATEGY_MAP.keys()))
    args = parser.parse_args()

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print(f"Loading embedding model {EMBED_MODEL_NAME} ...")
    model = SentenceTransformer(EMBED_MODEL_NAME)
    embedder = make_embedder(model)

    docs = load_docs(args.docs)
    print(f"Loaded {len(docs)} raw documents.")

    chunks = build_chunks(docs, args.strategy, embedder)
    print(f"Produced {len(chunks)} chunks using strategy='{args.strategy}'.")

    # persist chunks themselves for inspection/debugging
    chunks_path = os.path.join(PROCESSED_DIR, f"chunks_{args.strategy}.jsonl")
    with open(chunks_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    qdrant_path = os.path.join(PROCESSED_DIR, "qdrant_local")
    build_dense_index(chunks, model, qdrant_path)

    bm25_path = os.path.join(PROCESSED_DIR, "bm25_index.pkl")
    build_bm25_index(chunks, bm25_path)

    print("\nIngestion complete. Point app/core/config.py at:")
    print(f"  QDRANT_PATH = {qdrant_path}")
    print(f"  BM25_INDEX_PATH = {bm25_path}")


if __name__ == "__main__":
    main()
