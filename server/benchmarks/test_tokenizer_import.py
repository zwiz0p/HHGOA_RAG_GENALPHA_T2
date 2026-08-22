import sys
import gc
import psutil

def get_rss():
    gc.collect()
    return psutil.Process(psutil.Process().pid).memory_info().rss / (1024 * 1024)

print(f"Base RSS: {get_rss():.2f} MB")

# Set HuggingFace env vars to disable PyTorch detection
import os
os.environ["USE_TORCH"] = "0"
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
print(f"After AutoTokenizer RSS: {get_rss():.2f} MB")
print(f"Is torch in sys.modules? {'torch' in sys.modules}")
