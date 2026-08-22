"""
Legacy PyTorch Fallback Module.
This module is ONLY imported lazily if ONNX model artifacts are missing.
Keeping PyTorch imports inside this isolated module ensures that the production
ONNX path NEVER imports PyTorch C++ engines or sentence_transformers.
"""
from typing import Any

def get_pytorch_embedder(model_name: str) -> Any:
    import torch
    torch.set_num_threads(4)
    torch.set_grad_enabled(False)
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer(model_name)
    embedder.eval()
    return embedder

def get_pytorch_reranker(model_name: str) -> Any:
    import torch
    torch.set_num_threads(4)
    torch.set_grad_enabled(False)
    from sentence_transformers import CrossEncoder
    reranker = CrossEncoder(model_name)
    reranker.model.eval()
    return reranker
