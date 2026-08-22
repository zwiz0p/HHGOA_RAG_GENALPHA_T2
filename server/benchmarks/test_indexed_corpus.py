import os
import sys
import time
import json
import psutil
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core import config

class IndexedCorpusLookup:
    """
    Ultra-fast disk-backed JSONL corpus reader using binary file seek offsets.
    RAM Footprint: ~1.37 MB (offsets uint64 array)
    Lookup Latency: <0.05 ms per item
    """
    def __init__(self, jsonl_path: str, offset_path: str = None):
        self.jsonl_path = jsonl_path
        if offset_path is None:
            offset_path = jsonl_path + ".offsets.npy"
        self.offset_path = offset_path

        if not os.path.exists(self.offset_path):
            self._build_offsets()

        # Load uint64 binary offsets array into memory or mmap
        self.offsets = np.load(self.offset_path, mmap_mode="r")
        self.num_chunks = len(self.offsets)
        self._file = None

    def _build_offsets(self):
        print(f"Building byte offsets index for {self.jsonl_path}...")
        t0 = time.perf_counter()
        offsets = []
        with open(self.jsonl_path, "rb") as f:
            offset = 0
            for line in f:
                offsets.append(offset)
                offset += len(line)
        arr = np.array(offsets, dtype=np.uint64)
        np.save(self.offset_path, arr)
        t_elapsed = (time.perf_counter() - t0) * 1000
        print(f"Built {len(arr)} offsets in {t_elapsed:.2f}ms. Saved to {self.offset_path} ({os.path.getsize(self.offset_path)/(1024*1024):.2f} MB)")

    def _get_file(self):
        if self._file is None or self._file.closed:
            self._file = open(self.jsonl_path, "rb")
        return self._file

    def get_chunk(self, idx: int) -> dict:
        if idx < 0 or idx >= self.num_chunks:
            raise IndexError(f"Chunk index {idx} out of range (0..{self.num_chunks-1})")
        f = self._get_file()
        f.seek(int(self.offsets[idx]))
        line = f.readline()
        return json.loads(line.decode("utf-8"))

    def __getitem__(self, idx: int) -> dict:
        return self.get_chunk(idx)

    def __len__(self):
        return self.num_chunks

def test_lookup():
    jsonl_path = config.CHUNKS_PATH
    print("Testing IndexedCorpusLookup...")

    # 1. Measure RAM of building/loading IndexedCorpusLookup
    gc_0 = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    lookup = IndexedCorpusLookup(jsonl_path)
    gc_1 = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    print(f"IndexedCorpusLookup RAM footprint: +{gc_1 - gc_0:.2f} MB (Total items: {len(lookup)})")

    # 2. Benchmark seek read latency
    test_indices = [0, 100, 5000, 50000, 100000, 150000, 172363]
    latencies = []
    for idx in test_indices:
        t0 = time.perf_counter()
        chunk = lookup[idx]
        t_ms = (time.perf_counter() - t0) * 1000
        latencies.append(t_ms)
        print(f"Index {idx:6d} -> Chunk ID: {chunk.get('chunk_id')} | Read Time: {t_ms:.4f} ms")

    avg_lat = sum(latencies) / len(latencies)
    print(f"Average Single-Item Seek & Read Latency: {avg_lat:.4f} ms")

    # Benchmark 20 items batch lookup
    t0 = time.perf_counter()
    batch_20 = [lookup[i] for i in range(100, 120)]
    t_20_ms = (time.perf_counter() - t0) * 1000
    print(f"Batch 20 Chunks Retrieval Latency: {t_20_ms:.3f} ms")

if __name__ == "__main__":
    test_lookup()
