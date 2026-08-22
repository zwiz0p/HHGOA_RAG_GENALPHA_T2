"""
Exports Qdrant vectors into a memory-mapped NumPy matrix (dense_vectors.npy)
and chunks index for ultra-fast <15ms in-memory matrix multiplication on CPU.

Usage:
    python -m ingestion.export_dense_matrix
"""

import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.deps import get_qdrant_client
from app.core import config

OUT_MATRIX_PATH = os.path.join(config.BASE_DIR, "data", "processed", "dense_vectors.npy")


def export_vectors():
    client = get_qdrant_client()
    print(f"Connecting to Qdrant collection: {config.QDRANT_COLLECTION}...")
    t0 = time.perf_counter()

    total_count = client.count(collection_name=config.QDRANT_COLLECTION).count
    print(f"Total points to export: {total_count}")

    # Allocate NumPy array (N, 384) float32
    vectors = np.zeros((total_count, 384), dtype=np.float32)
    
    offset = None
    batch_size = 2000
    collected = 0

    print("Scrolling vectors from local Qdrant...")
    while collected < total_count:
        records, next_offset = client.scroll(
            collection_name=config.QDRANT_COLLECTION,
            limit=batch_size,
            offset=offset,
            with_vectors=True,
            with_payload=False,
        )
        if not records:
            break

        for r in records:
            idx = int(r.id)
            if idx < total_count and r.vector is not None:
                vectors[idx] = r.vector
                collected += 1

        offset = next_offset
        if collected % 20000 == 0 or collected == total_count:
            print(f"  Exported {collected}/{total_count} vectors ({time.perf_counter()-t0:.1f}s)...")

        if next_offset is None:
            break

    # Normalize vectors for fast cosine similarity via dot-product
    print("Normalizing vector matrix for cosine dot-product...")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    vectors = vectors / norms

    print(f"Saving contiguous matrix to {OUT_MATRIX_PATH} ({vectors.nbytes / 1e6:.1f} MB)...")
    np.save(OUT_MATRIX_PATH, vectors)
    print(f"Export complete in {time.perf_counter()-t0:.2f}s!")


if __name__ == "__main__":
    export_vectors()
