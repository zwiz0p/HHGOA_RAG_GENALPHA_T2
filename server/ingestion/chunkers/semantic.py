"""
Strategy 3 — Semantic (embedding-drift) chunking.

Embeds each sentence, walks through consecutive sentences, and cuts a new
chunk when cosine similarity between consecutive sentence embeddings drops
below a threshold (i.e. topic shift detected). More expensive at index time
than fixed/sentence chunking, but produces topically coherent chunks —
matters most for the longer/denser passages in the dataset.

Takes an `embedder` callable (List[str] -> np.ndarray) so this file has no
hard dependency on a specific embedding model — inject sentence-transformers,
an API-based embedder, whatever ingestion/embed_and_index.py wires up.
"""

from typing import List, Dict, Callable
import numpy as np

from .sentence_aware import split_sentences


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def chunk(text: str, embedder: Callable[[List[str]], np.ndarray], similarity_threshold: float = 0.55) -> List[str]:
    sentences = split_sentences(text)
    if len(sentences) <= 1:
        return [text]

    embeddings = embedder(sentences)

    chunks = []
    current = [sentences[0]]

    for i in range(1, len(sentences)):
        sim = cosine_sim(embeddings[i - 1], embeddings[i])
        if sim < similarity_threshold:
            chunks.append(" ".join(current))
            current = []
        current.append(sentences[i])

    if current:
        chunks.append(" ".join(current))

    return chunks


def chunk_document(doc: Dict, embedder: Callable[[List[str]], np.ndarray], similarity_threshold: float = 0.55) -> List[Dict]:
    pieces = chunk(doc["text"], embedder, similarity_threshold)
    out = []
    for i, piece in enumerate(pieces):
        c = dict(doc)
        c["text"] = piece
        c["chunk_id"] = f"{doc['doc_id']}_sem_{i}"
        c["chunk_strategy"] = "semantic"
        c["chunk_position"] = i
        out.append(c)
    return out
